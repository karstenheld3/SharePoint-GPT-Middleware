# Crawler Router V2 - SharePoint crawl, download, process, embed operations
# Implements _V2_IMPL_CRAWLER_B.md specification

import asyncio, datetime, json, os, shutil, textwrap, zipfile
from dataclasses import asdict, dataclass
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v2.common_ui_functions_v2 import generate_router_docs_page, generate_endpoint_docs, json_result, html_result, generate_ui_page
from routers_v2.common_logging_functions_v2 import MiddlewareLogger
from routers_v2.common_job_functions_v2 import list_jobs, StreamingJobWriter, ControlAction
from routers_v2.common_crawler_functions_v2 import DomainConfig, FileSource, ListSource, SitePageSource, load_domain, get_sources_for_scope, get_source_folder_path, get_embedded_folder_path, get_failed_folder_path, get_originals_folder_path, server_relative_url_to_local_path, get_file_relative_path, get_map_filename, cleanup_temp_map_files, is_file_embeddable, filter_embeddable_files, load_files_metadata, save_files_metadata, update_files_metadata, get_domain_path, SOURCE_TYPE_FOLDERS
from routers_v2.common_map_file_functions_v2 import SharePointMapRow, FilesMapRow, VectorStoreMapRow, ChangeDetectionResult, MapFileWriter, read_sharepoint_map, read_files_map, read_vectorstore_map, detect_changes, is_file_changed, is_file_changed_for_embed, sharepoint_map_row_to_files_map_row, files_map_row_to_vectorstore_map_row
from routers_v2.common_sharepoint_functions_v2 import SharePointFile, connect_to_site_using_client_id_and_certificate, try_get_document_library, get_document_library_files, download_file_from_sharepoint, get_list_items, export_list_to_csv, get_site_pages, download_site_page_html
from routers_v2.common_embed_functions_v2 import upload_file_to_openai, delete_file_from_openai, add_file_to_vector_store, remove_file_from_vector_store, list_vector_store_files, wait_for_vector_store_ready, get_failed_embeddings, upload_and_embed_file, remove_and_delete_file

router = APIRouter()
config = None
router_prefix = None
router_name = "crawler"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="/v2/domains?format=ui">Domains</a>'

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

def get_persistent_storage_path() -> str:
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''

def get_openai_client():
  return getattr(config, 'openai_client', None)

def get_crawler_config() -> dict:
  return {"client_id": getattr(config, 'SHAREPOINT_CLIENT_ID', ''), "tenant_id": getattr(config, 'SHAREPOINT_TENANT_ID', ''), "cert_path": getattr(config, 'SHAREPOINT_CERT_PATH', ''), "cert_password": getattr(config, 'SHAREPOINT_CERT_PASSWORD', '')}

@dataclass
class DownloadResult:
  source_id: str
  source_type: str
  total_files: int
  downloaded: int
  skipped: int
  errors: int
  removed: int

@dataclass
class ProcessResult:
  source_id: str
  source_type: str
  total_files: int
  processed: int
  skipped: int
  errors: int

@dataclass
class EmbedResult:
  source_id: str
  source_type: str
  total_files: int
  uploaded: int
  embedded: int
  failed: int
  removed: int

@dataclass
class IntegrityResult:
  source_id: str
  files_verified: int
  missing_redownloaded: int
  orphans_deleted: int
  wrong_path_moved: int

def _get_utc_now() -> tuple[str, int]:
  now = datetime.datetime.now(datetime.timezone.utc)
  return now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'), int(now.timestamp())

def _sharepoint_file_to_map_row(sp_file: SharePointFile) -> SharePointMapRow:
  return SharePointMapRow(sharepoint_listitem_id=sp_file.sharepoint_listitem_id, sharepoint_unique_file_id=sp_file.sharepoint_unique_file_id, filename=sp_file.filename, file_type=sp_file.file_type, file_size=sp_file.file_size, url=sp_file.url, raw_url=sp_file.raw_url, server_relative_url=sp_file.server_relative_url, last_modified_utc=sp_file.last_modified_utc, last_modified_timestamp=sp_file.last_modified_timestamp)

async def step_download_source(storage_path: str, domain: DomainConfig, source, source_type: str, mode: str, dry_run: bool, retry_batches: int, writer: StreamingJobWriter, logger: MiddlewareLogger, crawler_config: dict, job_id: str = None) -> DownloadResult:
  source_id = source.source_id
  logger.log_function_output(f"Download source '{source_id}' (type={source_type}, mode={mode}, dry_run={dry_run})")
  result = DownloadResult(source_id=source_id, source_type=source_type, total_files=0, downloaded=0, skipped=0, errors=0, removed=0)
  source_folder = get_source_folder_path(storage_path, domain.domain_id, source_type, source_id)
  os.makedirs(source_folder, exist_ok=True)
  temp_job_id = job_id if dry_run else None
  sp_map_name = get_map_filename(CRAWLER_HARDCODED_CONFIG.SHAREPOINT_MAP_CSV, temp_job_id)
  files_map_name = get_map_filename(CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV, temp_job_id)
  sp_map_path = os.path.join(source_folder, sp_map_name)
  files_map_path = os.path.join(source_folder, files_map_name)
  existing_files_map_path = os.path.join(source_folder, CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV)
  local_items = read_files_map(existing_files_map_path) if mode == "incremental" and os.path.exists(existing_files_map_path) else []
  try:
    ctx = connect_to_site_using_client_id_and_certificate(source.site_url, crawler_config['client_id'], crawler_config['tenant_id'], crawler_config['cert_path'], crawler_config['cert_password'])
    sp_files = []
    if source_type == "file_sources":
      library, error = try_get_document_library(ctx, source.site_url, source.sharepoint_url_part)
      if error:
        logger.log_function_output(f"  ERROR: {error}")
        result.errors = 1
        return result
      sp_files = get_document_library_files(ctx, library, source.filter, logger)
    elif source_type == "sitepage_sources":
      sp_files = get_site_pages(ctx, source.sharepoint_url_part, source.filter, logger)
    sp_items = [_sharepoint_file_to_map_row(f) for f in sp_files]
    result.total_files = len(sp_items)
    sp_writer = MapFileWriter(sp_map_path, SharePointMapRow)
    sp_writer.write_header()
    for item in sp_items: sp_writer.append_row(item)
    sp_writer.finalize()
    changes = detect_changes(sp_items, local_items)
    logger.log_function_output(f"  Change detection: added={len(changes.added)}, changed={len(changes.changed)}, removed={len(changes.removed)}, unchanged={len(changes.unchanged)}")
    target_folder = get_embedded_folder_path(storage_path, domain.domain_id, source_type, source_id) if source_type == "file_sources" else get_originals_folder_path(storage_path, domain.domain_id, source_type, source_id)
    os.makedirs(target_folder, exist_ok=True)
    files_writer = MapFileWriter(files_map_path, FilesMapRow)
    files_writer.write_header()
    to_download = changes.added + changes.changed
    total = len(to_download)
    for i, sp_item in enumerate(to_download):
      async for control in writer.check_control():
        if control == ControlAction.CANCEL:
          files_writer.finalize()
          return result
      local_path = server_relative_url_to_local_path(sp_item.server_relative_url, source.sharepoint_url_part)
      target_path = os.path.join(target_folder, local_path)
      utc_now, ts_now = _get_utc_now()
      logger.log_function_output(f"[ {i+1} / {total} ] Downloading '{sp_item.filename}'...")
      subfolder = CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_EMBEDDED_SUBFOLDER if source_type == "file_sources" else CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_ORIGINALS_SUBFOLDER
      if dry_run:
        logger.log_function_output(f"  [DRY RUN] Would download")
        file_rel_path = get_file_relative_path(domain.domain_id, source_type, source_id, subfolder, local_path)
        files_row = sharepoint_map_row_to_files_map_row(sp_item, file_rel_path, utc_now, ts_now)
        files_writer.append_row(files_row)
        result.downloaded += 1
      else:
        success, error = download_file_from_sharepoint(ctx, sp_item.server_relative_url, target_path, True, sp_item.last_modified_timestamp)
        if success:
          logger.log_function_output("  OK.")
          file_rel_path = get_file_relative_path(domain.domain_id, source_type, source_id, subfolder, local_path)
          files_row = sharepoint_map_row_to_files_map_row(sp_item, file_rel_path, utc_now, ts_now)
          files_writer.append_row(files_row)
          result.downloaded += 1
        else:
          logger.log_function_output(f"  ERROR: {error}")
          files_row = sharepoint_map_row_to_files_map_row(sp_item, "", utc_now, ts_now, sharepoint_error=error)
          files_writer.append_row(files_row)
          result.errors += 1
    for local_item in changes.unchanged:
      files_writer.append_row(local_item)
      result.skipped += 1
    for removed_item in changes.removed:
      if not dry_run and removed_item.file_relative_path:
        removed_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER, removed_item.file_relative_path)
        if os.path.exists(removed_path): os.remove(removed_path)
      result.removed += 1
    files_writer.finalize()
    logger.log_function_output(f"  Download complete: {result.downloaded} downloaded, {result.skipped} skipped, {result.errors} errors")
  except Exception as e:
    logger.log_function_output(f"  ERROR: {str(e)}")
    result.errors += 1
  return result

async def step_integrity_check(storage_path: str, domain_id: str, source, source_type: str, dry_run: bool, writer: StreamingJobWriter, logger: MiddlewareLogger, crawler_config: dict, job_id: str = None) -> IntegrityResult:
  source_id = source.source_id
  logger.log_function_output(f"Integrity check for source '{source_id}'")
  result = IntegrityResult(source_id=source_id, files_verified=0, missing_redownloaded=0, orphans_deleted=0, wrong_path_moved=0)
  source_folder = get_source_folder_path(storage_path, domain_id, source_type, source_id)
  temp_job_id = job_id if dry_run else None
  files_map_name = get_map_filename(CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV, temp_job_id)
  files_map_path = os.path.join(source_folder, files_map_name)
  if not os.path.exists(files_map_path):
    logger.log_function_output(f"  No files_map.csv found")
    return result
  local_items = read_files_map(files_map_path)
  target_folder = get_embedded_folder_path(storage_path, domain_id, source_type, source_id) if source_type == "file_sources" else get_originals_folder_path(storage_path, domain_id, source_type, source_id)
  for item in local_items:
    if not item.file_relative_path: continue
    expected_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER, item.file_relative_path)
    if os.path.exists(expected_path): result.files_verified += 1
    else: result.missing_redownloaded += 1
  if result.missing_redownloaded == 0: logger.log_function_output(f"  Integrity check passed: {result.files_verified} files verified")
  else: logger.log_function_output(f"  Integrity issues: {result.missing_redownloaded} missing files")
  return result

async def step_process_source(storage_path: str, domain_id: str, source, source_type: str, dry_run: bool, writer: StreamingJobWriter, logger: MiddlewareLogger, job_id: str = None) -> ProcessResult:
  source_id = source.source_id
  logger.log_function_output(f"Process source '{source_id}'")
  result = ProcessResult(source_id=source_id, source_type=source_type, total_files=0, processed=0, skipped=0, errors=0)
  if source_type == "file_sources":
    logger.log_function_output(f"  Skipping: file_sources do not require processing")
    return result
  originals_folder = get_originals_folder_path(storage_path, domain_id, source_type, source_id)
  embedded_folder = get_embedded_folder_path(storage_path, domain_id, source_type, source_id)
  os.makedirs(embedded_folder, exist_ok=True)
  if not os.path.exists(originals_folder): return result
  for filename in os.listdir(originals_folder):
    result.total_files += 1
    source_path = os.path.join(originals_folder, filename)
    if source_type == "list_sources":
      target_name = filename.rsplit('.', 1)[0] + '.md'
      target_path = os.path.join(embedded_folder, target_name)
      if dry_run:
        logger.log_function_output(f"  [DRY RUN] Would process '{filename}'")
        result.processed += 1
      else:
        try:
          with open(source_path, 'r', encoding='utf-8') as f: content = f.read()
          with open(target_path, 'w', encoding='utf-8') as f: f.write(f"# {filename}\n\n```\n{content}\n```\n")
          result.processed += 1
        except Exception as e:
          result.errors += 1
    elif source_type == "sitepage_sources":
      target_path = os.path.join(embedded_folder, filename)
      if dry_run: result.processed += 1
      else:
        try:
          shutil.copy2(source_path, target_path)
          result.processed += 1
        except: result.errors += 1
  return result

async def step_embed_source(storage_path: str, domain: DomainConfig, source, source_type: str, mode: str, dry_run: bool, retry_batches: int, writer: StreamingJobWriter, logger: MiddlewareLogger, openai_client, job_id: str = None) -> EmbedResult:
  source_id = source.source_id
  vector_store_id = domain.vector_store_id
  logger.log_function_output(f"Embed source '{source_id}' to vector store '{vector_store_id}'")
  result = EmbedResult(source_id=source_id, source_type=source_type, total_files=0, uploaded=0, embedded=0, failed=0, removed=0)
  source_folder = get_source_folder_path(storage_path, domain.domain_id, source_type, source_id)
  embedded_folder = get_embedded_folder_path(storage_path, domain.domain_id, source_type, source_id)
  failed_folder = get_failed_folder_path(storage_path, domain.domain_id, source_type, source_id)
  os.makedirs(failed_folder, exist_ok=True)
  temp_job_id = job_id if dry_run else None
  files_map_name = get_map_filename(CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV, temp_job_id)
  files_map_path = os.path.join(source_folder, files_map_name)
  if not os.path.exists(files_map_path): files_map_path = os.path.join(source_folder, CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV)
  if not os.path.exists(files_map_path): return result
  files_items = read_files_map(files_map_path)
  embeddable, skipped = filter_embeddable_files(files_items)
  result.total_files = len(embeddable)
  vs_map_path = os.path.join(source_folder, CRAWLER_HARDCODED_CONFIG.VECTOR_STORE_MAP_CSV)
  existing_vs_items = read_vectorstore_map(vs_map_path) if mode == "incremental" and os.path.exists(vs_map_path) else []
  vs_by_uid = {item.sharepoint_unique_file_id: item for item in existing_vs_items}
  vs_map_name = get_map_filename(CRAWLER_HARDCODED_CONFIG.VECTOR_STORE_MAP_CSV, temp_job_id)
  new_vs_map_path = os.path.join(source_folder, vs_map_name)
  vs_writer = MapFileWriter(new_vs_map_path, VectorStoreMapRow)
  vs_writer.write_header()
  metadata_entries = []
  total = len(embeddable)
  for i, files_item in enumerate(embeddable):
    async for control in writer.check_control():
      if control == ControlAction.CANCEL:
        vs_writer.finalize()
        return result
    logger.log_function_output(f"[ {i+1} / {total} ] Embedding '{files_item.filename}'...")
    existing_vs = vs_by_uid.get(files_item.sharepoint_unique_file_id)
    if existing_vs and not is_file_changed_for_embed(files_item, existing_vs):
      logger.log_function_output("  Skipped (unchanged)")
      vs_writer.append_row(existing_vs)
      result.uploaded += 1
      result.embedded += 1
      continue
    file_path = os.path.join(storage_path, CRAWLER_HARDCODED_CONFIG.PERSISTENT_STORAGE_PATH_CRAWLER_SUBFOLDER, files_item.file_relative_path)
    if not os.path.exists(file_path):
      logger.log_function_output(f"  ERROR: File not found")
      result.failed += 1
      continue
    utc_now, ts_now = _get_utc_now()
    if dry_run:
      logger.log_function_output(f"  [DRY RUN] Would embed")
      vs_row = files_map_row_to_vectorstore_map_row(files_item, "dry_run_file_id", vector_store_id, utc_now, ts_now, utc_now, ts_now)
      vs_writer.append_row(vs_row)
      result.uploaded += 1
      result.embedded += 1
    else:
      if existing_vs and existing_vs.openai_file_id:
        await remove_and_delete_file(openai_client, vector_store_id, existing_vs.openai_file_id, logger)
        result.removed += 1
      file_id, error = await upload_and_embed_file(openai_client, vector_store_id, file_path, logger)
      if error:
        logger.log_function_output(f"  ERROR: {error}")
        vs_row = files_map_row_to_vectorstore_map_row(files_item, "", vector_store_id, utc_now, ts_now, "", 0, embedding_error=error)
        vs_writer.append_row(vs_row)
        result.failed += 1
      else:
        logger.log_function_output("  OK.")
        embed_utc, embed_ts = _get_utc_now()
        vs_row = files_map_row_to_vectorstore_map_row(files_item, file_id, vector_store_id, utc_now, ts_now, embed_utc, embed_ts)
        vs_writer.append_row(vs_row)
        result.uploaded += 1
        result.embedded += 1
        metadata_entries.append({"sharepoint_listitem_id": files_item.sharepoint_listitem_id, "sharepoint_unique_file_id": files_item.sharepoint_unique_file_id, "openai_file_id": file_id, "file_relative_path": files_item.file_relative_path, "filename": files_item.filename, "file_type": files_item.file_type, "file_size": files_item.file_size, "last_modified_utc": files_item.last_modified_utc, "embedded_utc": embed_utc, "source_id": source_id, "source_type": source_type})
  vs_writer.finalize()
  if metadata_entries and not dry_run:
    domain_path = get_domain_path(storage_path, domain.domain_id)
    update_files_metadata(domain_path, metadata_entries)
  logger.log_function_output(f"  Embed complete: {result.embedded} embedded, {result.failed} failed")
  return result

async def crawl_domain(storage_path: str, domain: DomainConfig, mode: str, scope: str, source_id: Optional[str], dry_run: bool, retry_batches: int, writer: StreamingJobWriter, logger: MiddlewareLogger, crawler_config: dict, openai_client) -> dict:
  sources = get_sources_for_scope(domain, scope, source_id)
  if not sources:
    logger.log_function_output("WARNING: No sources configured")
    return {"ok": True, "data": {"sources_processed": 0}}
  logger.log_function_output(f"Crawling {len(sources)} source(s)")
  job_id = writer.job_id if dry_run else None
  download_results, embed_results = [], []
  for source_type, source in sources:
    result = await step_download_source(storage_path, domain, source, source_type, mode, dry_run, retry_batches, writer, logger, crawler_config, job_id)
    download_results.append(result)
    await step_integrity_check(storage_path, domain.domain_id, source, source_type, dry_run, writer, logger, crawler_config, job_id)
    if source_type in ("list_sources", "sitepage_sources"):
      await step_process_source(storage_path, domain.domain_id, source, source_type, dry_run, writer, logger, job_id)
    result = await step_embed_source(storage_path, domain, source, source_type, mode, dry_run, retry_batches, writer, logger, openai_client, job_id)
    embed_results.append(result)
  total_downloaded = sum(r.downloaded for r in download_results)
  total_embedded = sum(r.embedded for r in embed_results)
  total_errors = sum(r.errors for r in download_results) + sum(r.failed for r in embed_results)
  return {"ok": total_errors == 0, "error": f"{total_errors} errors" if total_errors > 0 else "", "data": {"domain_id": domain.domain_id, "mode": mode, "scope": scope, "dry_run": dry_run, "sources_processed": len(sources), "total_downloaded": total_downloaded, "total_embedded": total_embedded, "total_errors": total_errors}}

def create_crawl_report(storage_path: str, domain_id: str, mode: str, scope: str, results: dict, started_utc: str, finished_utc: str) -> str:
  timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')
  report_id = f"crawls/{timestamp}_{domain_id}_{scope}_{mode}"
  reports_folder = os.path.join(storage_path, "reports", "crawls")
  os.makedirs(reports_folder, exist_ok=True)
  report = {"report_id": report_id, "title": f"Crawl Report: {domain_id}", "type": "crawl", "created_utc": finished_utc, "ok": results.get("ok", False), "parameters": {"domain_id": domain_id, "mode": mode, "scope": scope}, "timing": {"started_utc": started_utc, "finished_utc": finished_utc}, "data": results.get("data", {})}
  zip_path = os.path.join(reports_folder, f"{timestamp}_{domain_id}_{scope}_{mode}.zip")
  with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf: zf.writestr("report.json", json.dumps(report, indent=2))
  return report_id


# ----------------------------------------- START: Router Endpoints ---------------------------------------------------

@router.get(f"/{router_name}")
async def crawler_root(request: Request):
  """Crawler Router - Monitor and control SharePoint crawl jobs."""
  logger = MiddlewareLogger.create()
  logger.log_function_header("crawler_root")
  format_param = request.query_params.get("format", "json")
  all_jobs = list_jobs(get_persistent_storage_path())
  crawler_jobs = [j for j in all_jobs if f"/{router_name}/" in (j.source_url or "")]
  if format_param == "ui":
    logger.log_function_footer()
    return HTMLResponse(_generate_crawler_ui_page([asdict(j) for j in crawler_jobs]))
  if format_param == "json":
    logger.log_function_footer()
    return json_result(True, "", [asdict(j) for j in crawler_jobs])
  if format_param == "html":
    logger.log_function_footer()
    return html_result("Crawler Jobs", {"jobs": [asdict(j) for j in crawler_jobs]}, main_page_nav_html)
  logger.log_function_footer()
  return generate_router_docs_page(router_name, "Crawler router for SharePoint crawl operations", router_prefix)

@router.get(f"/{router_name}/crawl")
async def crawler_crawl(request: Request):
  """Full crawl: download + process + embed. Params: domain_id (required), mode, scope, source_id, format, dry_run, retry_batches"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("crawler_crawl")
  if len(request.query_params) == 0:
    logger.log_function_footer()
    return PlainTextResponse(generate_endpoint_docs("Full crawl endpoint. Required: domain_id. Optional: mode=full|incremental, scope=all|files|lists|sitepages, dry_run=true|false, retry_batches=2", router_prefix), media_type="text/plain; charset=utf-8")
  params = dict(request.query_params)
  domain_id = params.get("domain_id")
  if not domain_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'domain_id' parameter.", {})
  try:
    domain = load_domain(get_persistent_storage_path(), domain_id, logger)
  except FileNotFoundError:
    logger.log_function_footer()
    return json_result(False, f"Domain '{domain_id}' not found.", {})
  mode = params.get("mode", "full")
  scope = params.get("scope", "all")
  source_id = params.get("source_id")
  format_param = params.get("format", "json")
  dry_run = params.get("dry_run", "false").lower() == "true"
  retry_batches = int(params.get("retry_batches", "2"))
  if format_param == "stream":
    return StreamingResponse(_crawl_stream(domain, mode, scope, source_id, dry_run, retry_batches, logger), media_type="text/event-stream")
  logger.log_function_footer()
  return json_result(False, "Use format=stream for crawl operations.", {})

async def _crawl_stream(domain: DomainConfig, mode: str, scope: str, source_id: Optional[str], dry_run: bool, retry_batches: int, logger: MiddlewareLogger):
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="crawl", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/crawl?domain_id={domain.domain_id}&mode={mode}&scope={scope}&dry_run={dry_run}", router_prefix=router_prefix, metadata={"domain_id": domain.domain_id, "vector_store_id": domain.vector_store_id, "mode": mode, "scope": scope, "source_id": source_id, "dry_run": dry_run, "retry_batches": retry_batches})
  logger.stream_job_writer = writer
  started_utc, _ = _get_utc_now()
  try:
    yield writer.emit_start()
    yield logger.log_function_output(f"Starting crawl for domain '{domain.domain_id}'")
    results = await crawl_domain(get_persistent_storage_path(), domain, mode, scope, source_id, dry_run, retry_batches, writer, logger, get_crawler_config(), get_openai_client())
    finished_utc, _ = _get_utc_now()
    if not dry_run and results.get("ok", False):
      report_id = create_crawl_report(get_persistent_storage_path(), domain.domain_id, mode, scope, results, started_utc, finished_utc)
      results["data"]["report_id"] = report_id
    yield logger.log_function_output(f"Crawl completed: {results.get('data', {}).get('total_embedded', 0)} files embedded")
    yield writer.emit_end(ok=results.get("ok", False), error=results.get("error", ""), data=results.get("data", {}))
  except Exception as e:
    yield logger.log_function_output(f"ERROR: {str(e)}")
    yield writer.emit_end(ok=False, error=str(e), data={})
  finally:
    if dry_run:
      for source_type, source in get_sources_for_scope(domain, scope, source_id):
        cleanup_temp_map_files(get_source_folder_path(get_persistent_storage_path(), domain.domain_id, source_type, source.source_id), writer.job_id)
    writer.finalize()

@router.get(f"/{router_name}/download_data")
async def crawler_download_data(request: Request):
  """Download step only. Params: domain_id (required), mode, scope, source_id, format, dry_run, retry_batches"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("crawler_download_data")
  if len(request.query_params) == 0:
    logger.log_function_footer()
    return PlainTextResponse(generate_endpoint_docs("Download step only.", router_prefix), media_type="text/plain; charset=utf-8")
  params = dict(request.query_params)
  domain_id = params.get("domain_id")
  if not domain_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'domain_id' parameter.", {})
  try:
    domain = load_domain(get_persistent_storage_path(), domain_id, logger)
  except FileNotFoundError:
    logger.log_function_footer()
    return json_result(False, f"Domain '{domain_id}' not found.", {})
  mode, scope, source_id = params.get("mode", "full"), params.get("scope", "all"), params.get("source_id")
  format_param, dry_run = params.get("format", "json"), params.get("dry_run", "false").lower() == "true"
  retry_batches = int(params.get("retry_batches", "2"))
  if format_param == "stream":
    return StreamingResponse(_download_stream(domain, mode, scope, source_id, dry_run, retry_batches, logger), media_type="text/event-stream")
  logger.log_function_footer()
  return json_result(False, "Use format=stream.", {})

async def _download_stream(domain: DomainConfig, mode: str, scope: str, source_id: Optional[str], dry_run: bool, retry_batches: int, logger: MiddlewareLogger):
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="download_data", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/download_data?domain_id={domain.domain_id}", router_prefix=router_prefix, metadata={"domain_id": domain.domain_id, "vector_store_id": domain.vector_store_id, "mode": mode, "scope": scope, "source_id": source_id, "dry_run": dry_run, "retry_batches": retry_batches})
  logger.stream_job_writer = writer
  try:
    yield writer.emit_start()
    job_id = writer.job_id if dry_run else None
    results = []
    for source_type, source in get_sources_for_scope(domain, scope, source_id):
      result = await step_download_source(get_persistent_storage_path(), domain, source, source_type, mode, dry_run, retry_batches, writer, logger, get_crawler_config(), job_id)
      results.append(asdict(result))
    yield writer.emit_end(ok=True, data={"results": results})
  except Exception as e:
    yield writer.emit_end(ok=False, error=str(e), data={})
  finally:
    if dry_run:
      for source_type, source in get_sources_for_scope(domain, scope, source_id):
        cleanup_temp_map_files(get_source_folder_path(get_persistent_storage_path(), domain.domain_id, source_type, source.source_id), writer.job_id)
    writer.finalize()

@router.get(f"/{router_name}/process_data")
async def crawler_process_data(request: Request):
  """Process step only. Params: domain_id (required), scope, source_id, format, dry_run"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("crawler_process_data")
  if len(request.query_params) == 0:
    logger.log_function_footer()
    return PlainTextResponse(generate_endpoint_docs("Process step only.", router_prefix), media_type="text/plain; charset=utf-8")
  params = dict(request.query_params)
  domain_id = params.get("domain_id")
  if not domain_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'domain_id' parameter.", {})
  try:
    domain = load_domain(get_persistent_storage_path(), domain_id, logger)
  except FileNotFoundError:
    logger.log_function_footer()
    return json_result(False, f"Domain '{domain_id}' not found.", {})
  scope, source_id = params.get("scope", "all"), params.get("source_id")
  format_param, dry_run = params.get("format", "json"), params.get("dry_run", "false").lower() == "true"
  if format_param == "stream":
    return StreamingResponse(_process_stream(domain, scope, source_id, dry_run, logger), media_type="text/event-stream")
  logger.log_function_footer()
  return json_result(False, "Use format=stream.", {})

async def _process_stream(domain: DomainConfig, scope: str, source_id: Optional[str], dry_run: bool, logger: MiddlewareLogger):
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="process_data", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/process_data?domain_id={domain.domain_id}", router_prefix=router_prefix, metadata={"domain_id": domain.domain_id, "vector_store_id": domain.vector_store_id, "scope": scope, "source_id": source_id, "dry_run": dry_run})
  logger.stream_job_writer = writer
  try:
    yield writer.emit_start()
    job_id = writer.job_id if dry_run else None
    results = []
    for source_type, source in get_sources_for_scope(domain, scope, source_id):
      if source_type in ("list_sources", "sitepage_sources"):
        result = await step_process_source(get_persistent_storage_path(), domain.domain_id, source, source_type, dry_run, writer, logger, job_id)
        results.append(asdict(result))
    yield writer.emit_end(ok=True, data={"results": results})
  except Exception as e:
    yield writer.emit_end(ok=False, error=str(e), data={})
  finally:
    writer.finalize()

@router.get(f"/{router_name}/embed_data")
async def crawler_embed_data(request: Request):
  """Embed step only. Params: domain_id (required), mode, scope, source_id, format, dry_run, retry_batches"""
  logger = MiddlewareLogger.create()
  logger.log_function_header("crawler_embed_data")
  if len(request.query_params) == 0:
    logger.log_function_footer()
    return PlainTextResponse(generate_endpoint_docs("Embed step only.", router_prefix), media_type="text/plain; charset=utf-8")
  params = dict(request.query_params)
  domain_id = params.get("domain_id")
  if not domain_id:
    logger.log_function_footer()
    return json_result(False, "Missing 'domain_id' parameter.", {})
  try:
    domain = load_domain(get_persistent_storage_path(), domain_id, logger)
  except FileNotFoundError:
    logger.log_function_footer()
    return json_result(False, f"Domain '{domain_id}' not found.", {})
  mode, scope, source_id = params.get("mode", "full"), params.get("scope", "all"), params.get("source_id")
  format_param, dry_run = params.get("format", "json"), params.get("dry_run", "false").lower() == "true"
  retry_batches = int(params.get("retry_batches", "2"))
  if format_param == "stream":
    return StreamingResponse(_embed_stream(domain, mode, scope, source_id, dry_run, retry_batches, logger), media_type="text/event-stream")
  logger.log_function_footer()
  return json_result(False, "Use format=stream.", {})

async def _embed_stream(domain: DomainConfig, mode: str, scope: str, source_id: Optional[str], dry_run: bool, retry_batches: int, logger: MiddlewareLogger):
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="embed_data", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/embed_data?domain_id={domain.domain_id}", router_prefix=router_prefix, metadata={"domain_id": domain.domain_id, "vector_store_id": domain.vector_store_id, "mode": mode, "scope": scope, "source_id": source_id, "dry_run": dry_run, "retry_batches": retry_batches})
  logger.stream_job_writer = writer
  try:
    yield writer.emit_start()
    job_id = writer.job_id if dry_run else None
    results = []
    for source_type, source in get_sources_for_scope(domain, scope, source_id):
      result = await step_embed_source(get_persistent_storage_path(), domain, source, source_type, mode, dry_run, retry_batches, writer, logger, get_openai_client(), job_id)
      results.append(asdict(result))
    yield writer.emit_end(ok=True, data={"results": results})
  except Exception as e:
    yield writer.emit_end(ok=False, error=str(e), data={})
  finally:
    if dry_run:
      for source_type, source in get_sources_for_scope(domain, scope, source_id):
        cleanup_temp_map_files(get_source_folder_path(get_persistent_storage_path(), domain.domain_id, source_type, source.source_id), writer.job_id)
    writer.finalize()

# ----------------------------------------- END: Router Endpoints -----------------------------------------------------


# ----------------------------------------- START: UI Generation ------------------------------------------------------

def get_router_specific_js() -> str:
  return f"""
const jobsState = new Map();
document.addEventListener('DOMContentLoaded', async () => {{ await refreshJobsTable(); initConsoleResize(); }});
async function refreshJobsTable() {{
  try {{
    const response = await fetch('{router_prefix}/{router_name}?format=json');
    const result = await response.json();
    if (result.ok) {{ jobsState.clear(); result.data.forEach(job => jobsState.set(job.job_id, job)); renderAllJobs(); }}
    else {{ showToast('Load Failed', result.error, 'error'); }}
  }} catch (e) {{ showToast('Load Failed', e.message, 'error'); }}
}}
function reloadItems() {{ refreshJobsTable(); }}
function renderAllJobs() {{
  const jobs = Array.from(jobsState.values());
  const tbody = document.getElementById('items-tbody');
  if (jobs.length === 0) {{ tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No crawler jobs found</td></tr>'; }}
  else {{ tbody.innerHTML = jobs.map(job => renderJobRow(job)).join(''); }}
  const countEl = document.getElementById('item-count'); if (countEl) countEl.textContent = jobs.length;
}}
function renderJobRow(job) {{
  const meta = job.metadata || {{}};
  const action = job.action || '-';
  const domainId = meta.domain_id || '-';
  const vectorStoreId = meta.vector_store_id || '-';
  const mode = meta.mode || '-';
  const scope = meta.scope || '-';
  const sourceId = meta.source_id || '-';
  const actions = renderJobActions(job);
  const rowId = sanitizeId(job.job_id);
  const isRunning = job.state === 'running';
  const rowClass = isRunning ? 'row-running' : '';
  return `<tr id="job-${{rowId}}" class="${{rowClass}}"><td>${{escapeHtml(job.job_id)}}</td><td>${{escapeHtml(action)}}</td><td>${{escapeHtml(domainId)}}</td><td>${{escapeHtml(vectorStoreId)}}</td><td>${{escapeHtml(mode)}}</td><td>${{escapeHtml(scope)}}</td><td>${{escapeHtml(sourceId)}}</td><td>${{actions}}</td></tr>`;
}}
function renderJobActions(job) {{
  let html = `<button class="btn btn-sm" onclick="monitorJob('${{job.job_id}}')">Monitor</button>`;
  if (job.state === 'running') {{
    html += ` <button class="btn btn-sm" onclick="controlJob('${{job.job_id}}', 'pause')">Pause</button>`;
    html += ` <button class="btn btn-sm btn-danger" onclick="controlJob('${{job.job_id}}', 'cancel')">Cancel</button>`;
  }} else if (job.state === 'paused') {{
    html += ` <button class="btn btn-sm" onclick="controlJob('${{job.job_id}}', 'resume')">Resume</button>`;
    html += ` <button class="btn btn-sm btn-danger" onclick="controlJob('${{job.job_id}}', 'cancel')">Cancel</button>`;
  }}
  return html;
}}
function monitorJob(jobId) {{
  clearConsole();
  startSSE('{router_prefix}/jobs/monitor?job_id=' + encodeURIComponent(jobId) + '&format=stream');
}}
async function controlJob(jobId, action) {{
  try {{
    const response = await fetch('{router_prefix}/jobs/control?job_id=' + encodeURIComponent(jobId) + '&action=' + action, {{ method: 'POST' }});
    const result = await response.json();
    if (result.ok) {{ showToast('Success', 'Job ' + action + ' requested', 'success'); refreshJobsTable(); }}
    else {{ showToast('Failed', result.error, 'error'); }}
  }} catch (e) {{ showToast('Failed', e.message, 'error'); }}
}}
"""

def _generate_crawler_ui_page(jobs: list) -> str:
  """Generate crawler jobs UI using generate_ui_page like demorouter2."""
  columns = [
    {"field": "job_id", "header": "ID"},
    {"field": "action", "header": "Action", "default": "-"},
    {"field": "domain_id", "header": "Domain ID", "default": "-"},
    {"field": "vector_store_id", "header": "Vector Store ID", "default": "-"},
    {"field": "mode", "header": "Mode", "default": "-"},
    {"field": "scope", "header": "Scope", "default": "-"},
    {"field": "source_id", "header": "Source ID", "default": "-"},
    {"field": "state", "header": "State", "default": "-"},
    {"field": "actions", "header": "Actions", "buttons": [
      {"text": "Monitor", "onclick": "monitorJob('{itemId}')", "class": "btn-small"},
      {"text": "Pause", "onclick": "controlJob('{itemId}', 'pause')", "class": "btn-small", "show_if": "state === 'running'"},
      {"text": "Resume", "onclick": "controlJob('{itemId}', 'resume')", "class": "btn-small", "show_if": "state === 'paused'"},
      {"text": "Cancel", "onclick": "controlJob('{itemId}', 'cancel')", "class": "btn-small btn-delete", "show_if": "state === 'running' || state === 'paused'"}
    ]}
  ]
  
  # Flatten job metadata into row data
  items = []
  for job in jobs:
    meta = job.get("metadata", {}) or {}
    items.append({
      "job_id": job.get("job_id", ""),
      "action": meta.get("action", job.get("action", "-")),
      "domain_id": meta.get("domain_id", "-"),
      "vector_store_id": meta.get("vector_store_id", "-"),
      "mode": meta.get("mode", "-"),
      "scope": meta.get("scope", "-"),
      "source_id": meta.get("source_id", "-"),
      "state": job.get("state", "-")
    })
  
  return generate_ui_page(
    title="Crawler Jobs",
    router_prefix=router_prefix,
    items=items,
    columns=columns,
    row_id_field="job_id",
    row_id_prefix="job",
    navigation_html=main_page_nav_html,
    toolbar_buttons=[],
    enable_selection=False,
    enable_bulk_delete=False,
    list_endpoint=f"{router_prefix}/{router_name}?format=json",
    jobs_control_endpoint=f"{router_prefix}/jobs/control",
    additional_js=get_router_specific_js()
  )

# ----------------------------------------- END: UI Generation --------------------------------------------------------
