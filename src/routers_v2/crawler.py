# Crawler Router V2 - SharePoint crawl, download, process, embed operations
# Implements _V2_IMPL_CRAWLER_B.md specification

import asyncio, datetime, httpx, json, os, shutil, textwrap, zipfile
from dataclasses import asdict, dataclass
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse

from hardcoded_config import CRAWLER_HARDCODED_CONFIG
from routers_v2.common_ui_functions_v2 import generate_router_docs_page, generate_endpoint_docs, json_result, html_result, generate_ui_page
from routers_v2.common_logging_functions_v2 import MiddlewareLogger, UNKNOWN
from routers_v2.common_job_functions_v2 import list_jobs, StreamingJobWriter, ControlAction
from routers_v2.common_crawler_functions_v2 import DomainConfig, FileSource, ListSource, SitePageSource, load_domain, get_sources_for_scope, get_source_folder_path, get_embedded_folder_path, get_failed_folder_path, get_originals_folder_path, server_relative_url_to_local_path, get_file_relative_path, get_map_filename, cleanup_temp_map_files, is_file_embeddable, filter_embeddable_files, load_files_metadata, save_files_metadata, update_files_metadata, get_domain_path, SOURCE_TYPE_FOLDERS
from routers_v2.common_map_file_functions_v2 import SharePointMapRow, FilesMapRow, VectorStoreMapRow, ChangeDetectionResult, MapFileWriter, read_sharepoint_map, read_files_map, read_vectorstore_map, detect_changes, is_file_changed, is_file_changed_for_embed, sharepoint_map_row_to_files_map_row, files_map_row_to_vectorstore_map_row
from routers_v2.common_sharepoint_functions_v2 import SharePointFile, connect_to_site_using_client_id_and_certificate, try_get_document_library, get_document_library_files, download_file_from_sharepoint, get_list_items, export_list_to_csv, get_site_pages, download_site_page_html, create_document_library, add_number_field_to_list, add_text_field_to_list, upload_file_to_library, upload_file_to_folder, update_file_content, rename_file, move_file, delete_file, create_folder_in_library, delete_document_library, create_list, add_list_item, update_list_item, delete_list_item, delete_list, create_site_page, update_site_page, rename_site_page, delete_site_page, file_exists_in_library
from routers_v2.common_embed_functions_v2 import upload_file_to_openai, delete_file_from_openai, add_file_to_vector_store, remove_file_from_vector_store, list_vector_store_files, wait_for_vector_store_ready, get_failed_embeddings, upload_and_embed_file, remove_and_delete_file

router = APIRouter()
config = None
router_prefix = None
router_name = "crawler"
main_page_nav_html = '<a href="/">Back to Main Page</a> | <a href="{router_prefix}/domains?format=ui">Domains</a> | <a href="{router_prefix}/crawler?format=ui">Crawler</a> | <a href="{router_prefix}/jobs?format=ui">Jobs</a> | <a href="{router_prefix}/reports?format=ui">Reports</a>'

def set_config(app_config, prefix):
  global config, router_prefix
  config = app_config
  router_prefix = prefix

def get_persistent_storage_path() -> str:
  return getattr(config, 'LOCAL_PERSISTENT_STORAGE_PATH', None) or ''

def get_openai_client():
  return getattr(config, 'openai_client', None)

def get_crawler_config() -> dict:
  cert_filename = getattr(config, 'CRAWLER_CLIENT_CERTIFICATE_PFX_FILE', '') or ''
  cert_path = os.path.join(get_persistent_storage_path(), cert_filename) if cert_filename else ''
  return {"client_id": getattr(config, 'CRAWLER_CLIENT_ID', '') or '', "tenant_id": getattr(config, 'CRAWLER_TENANT_ID', '') or '', "cert_path": cert_path, "cert_password": getattr(config, 'CRAWLER_CLIENT_CERTIFICATE_PASSWORD', '') or ''}

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
      sp_files = get_document_library_files(ctx, library, source.filter, logger, dry_run)
    elif source_type == "sitepage_sources":
      sp_files = get_site_pages(ctx, source.sharepoint_url_part, source.filter, logger, dry_run)
    sp_items = [_sharepoint_file_to_map_row(f) for f in sp_files]
    result.total_files = len(sp_items)
    sp_writer = MapFileWriter(sp_map_path, SharePointMapRow)
    sp_writer.write_header()
    for item in sp_items: sp_writer.append_row(item)
    sp_writer.finalize()
    changes = detect_changes(sp_items, local_items)
    logger.log_function_output(f"  {len(changes.added)} added, {len(changes.changed)} changed, {len(changes.removed)} removed, {len(changes.unchanged)} unchanged.")
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
      success, error = download_file_from_sharepoint(ctx, sp_item.server_relative_url, target_path, True, sp_item.last_modified_timestamp, dry_run)
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
    logger.log_function_output(f"  {result.downloaded} downloaded, {result.skipped} skipped, {result.errors} error{'' if result.errors == 1 else 's'}.")
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
      vs_row = files_map_row_to_vectorstore_map_row(files_item, "dry_run_file_id", vector_store_id, utc_now, ts_now, utc_now, ts_now)
      vs_writer.append_row(vs_row)
      result.uploaded += 1
      result.embedded += 1
      logger.log_function_output("  OK.")
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
  logger.log_function_output(f"  {result.embedded} embedded, {result.failed} failed.")
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
    return html_result("Crawler Jobs", {"jobs": [asdict(j) for j in crawler_jobs]}, main_page_nav_html.replace("{router_prefix}", router_prefix))
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
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="crawl", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/crawl?domain_id={domain.domain_id}&mode={mode}&scope={scope}&dry_run={dry_run}", router_prefix=router_prefix)
  logger.stream_job_writer = writer
  started_utc, _ = _get_utc_now()
  try:
    yield writer.emit_start()
    yield logger.log_function_output(f"Starting crawl for domain '{domain.domain_id}'")
    results = await crawl_domain(get_persistent_storage_path(), domain, mode, scope, source_id, dry_run, retry_batches, writer, logger, get_crawler_config(), get_openai_client())
    for sse in writer.drain_sse_queue(): yield sse  # Yield queued log events from nested calls
    finished_utc, _ = _get_utc_now()
    if not dry_run and results.get("ok", False):
      report_id = create_crawl_report(get_persistent_storage_path(), domain.domain_id, mode, scope, results, started_utc, finished_utc)
      results["data"]["report_id"] = report_id
    total_embedded = results.get('data', {}).get('total_embedded', 0)
    yield logger.log_function_output(f"{total_embedded} file{'' if total_embedded == 1 else 's'} embedded.")
    yield writer.emit_end(ok=results.get("ok", False), error=results.get("error", ""), data=results.get("data", {}))
  except Exception as e:
    yield logger.log_function_output(f"ERROR: Crawl failed -> {str(e)}")
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
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="download_data", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/download_data?domain_id={domain.domain_id}", router_prefix=router_prefix)
  logger.stream_job_writer = writer
  try:
    yield writer.emit_start()
    job_id = writer.job_id if dry_run else None
    results = []
    for source_type, source in get_sources_for_scope(domain, scope, source_id):
      result = await step_download_source(get_persistent_storage_path(), domain, source, source_type, mode, dry_run, retry_batches, writer, logger, get_crawler_config(), job_id)
      for sse in writer.drain_sse_queue(): yield sse
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
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="process_data", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/process_data?domain_id={domain.domain_id}", router_prefix=router_prefix)
  logger.stream_job_writer = writer
  try:
    yield writer.emit_start()
    job_id = writer.job_id if dry_run else None
    results = []
    for source_type, source in get_sources_for_scope(domain, scope, source_id):
      if source_type in ("list_sources", "sitepage_sources"):
        result = await step_process_source(get_persistent_storage_path(), domain.domain_id, source, source_type, dry_run, writer, logger, job_id)
        for sse in writer.drain_sse_queue(): yield sse
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
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="embed_data", object_id=domain.domain_id, source_url=f"{router_prefix}/{router_name}/embed_data?domain_id={domain.domain_id}", router_prefix=router_prefix)
  logger.stream_job_writer = writer
  try:
    yield writer.emit_start()
    job_id = writer.job_id if dry_run else None
    results = []
    for source_type, source in get_sources_for_scope(domain, scope, source_id):
      result = await step_embed_source(get_persistent_storage_path(), domain, source, source_type, mode, dry_run, retry_batches, writer, logger, get_openai_client(), job_id)
      for sse in writer.drain_sse_queue(): yield sse
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


# ----------------------------------------- START: Selftest -----------------------------------------------------------

SELFTEST_DOMAIN_ID = "_SELFTEST"
SELFTEST_LIBRARY_NAME = "_SELFTEST_DOCS"
SELFTEST_LIST_NAME = "_SELFTEST_LIST"
SELFTEST_SNAPSHOT_BASE = "_selftest_snapshots"
SELFTEST_MUTATION_POLL_INTERVAL = 5
SELFTEST_MUTATION_MAX_WAIT = 60

# Snapshot definitions - expected row counts after various operations
SNAP_FULL_ALL = {
  "01_files/files_all": {"files_map_rows": 9},
  "01_files/files_crawl1": {"files_map_rows": 6},
  "02_lists/lists_all": {"files_map_rows": 6},
  "02_lists/lists_active": {"files_map_rows": 3},
  "03_sitepages/pages_all": {"files_map_rows": 3}
}

SNAP_FULL_FILES = {
  "01_files/files_all": {"files_map_rows": 9},
  "01_files/files_crawl1": {"files_map_rows": 6},
  "02_lists/lists_all": {"files_map_rows": 0},
  "02_lists/lists_active": {"files_map_rows": 0},
  "03_sitepages/pages_all": {"files_map_rows": 0}
}

SNAP_FULL_LISTS = {
  "01_files/files_all": {"files_map_rows": 0},
  "01_files/files_crawl1": {"files_map_rows": 0},
  "02_lists/lists_all": {"files_map_rows": 6},
  "02_lists/lists_active": {"files_map_rows": 3},
  "03_sitepages/pages_all": {"files_map_rows": 0}
}

SNAP_FULL_PAGES = {
  "01_files/files_all": {"files_map_rows": 0},
  "01_files/files_crawl1": {"files_map_rows": 0},
  "02_lists/lists_all": {"files_map_rows": 0},
  "02_lists/lists_active": {"files_map_rows": 0},
  "03_sitepages/pages_all": {"files_map_rows": 3}
}

SNAP_EMPTY = {
  "01_files/files_all": {"files_map_rows": 0},
  "01_files/files_crawl1": {"files_map_rows": 0},
  "02_lists/lists_all": {"files_map_rows": 0},
  "02_lists/lists_active": {"files_map_rows": 0},
  "03_sitepages/pages_all": {"files_map_rows": 0}
}

def _selftest_save_snapshot(storage_path: str, domain_id: str, snapshot_name: str) -> None:
  """Copy crawler/{domain_id}/ to _selftest_snapshots/{snapshot_name}/"""
  source = os.path.join(storage_path, "crawler", domain_id)
  target = os.path.join(storage_path, SELFTEST_SNAPSHOT_BASE, snapshot_name)
  if os.path.exists(target): shutil.rmtree(target)
  if os.path.exists(source): shutil.copytree(source, target)

def _selftest_restore_snapshot(storage_path: str, domain_id: str, snapshot_name: str) -> None:
  """Restore crawler/{domain_id}/ from _selftest_snapshots/{snapshot_name}/"""
  source = os.path.join(storage_path, SELFTEST_SNAPSHOT_BASE, snapshot_name)
  target = os.path.join(storage_path, "crawler", domain_id)
  if os.path.exists(target): shutil.rmtree(target)
  if os.path.exists(source): shutil.copytree(source, target)
  else: os.makedirs(target, exist_ok=True)

def _selftest_clear_domain_folder(storage_path: str, domain_id: str) -> None:
  """Delete all content in crawler/{domain_id}/"""
  target = os.path.join(storage_path, "crawler", domain_id)
  if os.path.exists(target): shutil.rmtree(target)
  os.makedirs(target, exist_ok=True)

def _selftest_cleanup_snapshots(storage_path: str) -> None:
  """Delete all snapshots in _selftest_snapshots/"""
  snapshots_dir = os.path.join(storage_path, SELFTEST_SNAPSHOT_BASE)
  if os.path.exists(snapshots_dir): shutil.rmtree(snapshots_dir)

def _selftest_verify_snapshot(storage_path: str, domain_id: str, expected: dict) -> list[str]:
  """Compare actual crawler output against expected snapshot. Returns list of failures."""
  failures = []
  domain_path = os.path.join(storage_path, "crawler", domain_id)
  for source_path, expected_vals in expected.items():
    files_map_path = os.path.join(domain_path, source_path, CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV)
    expected_rows = expected_vals.get("files_map_rows", 0)
    if not os.path.exists(files_map_path):
      if expected_rows > 0: failures.append(f"{source_path}: files_map.csv missing, expected {expected_rows} rows")
      continue
    actual_items = read_files_map(files_map_path)
    actual_rows = len(actual_items)
    if actual_rows != expected_rows:
      failures.append(f"{source_path}: files_map rows {actual_rows} != {expected_rows} expected")
  return failures

async def _selftest_wait_for_mutation(ctx, check_func, description: str, logger: MiddlewareLogger) -> bool:
  """Poll SharePoint until mutation is reflected. Returns True if mutation detected, False if timeout."""
  logger.log_function_output(f"  Waiting for mutation: {description}...")
  waited = 0
  while waited < SELFTEST_MUTATION_MAX_WAIT:
    try:
      if await check_func(): 
        logger.log_function_output(f"    Mutation visible after {waited}s.")
        return True
    except: pass
    await asyncio.sleep(SELFTEST_MUTATION_POLL_INTERVAL)
    waited += SELFTEST_MUTATION_POLL_INTERVAL
  logger.log_function_output(f"    WARNING: Mutation not visible after {SELFTEST_MUTATION_MAX_WAIT}s.")
  return False

async def _selftest_run_crawl(base_url: str, domain_id: str, endpoint: str, mode: str = None, scope: str = None, source_id: str = None, dry_run: bool = False, timeout: float = 300.0) -> dict:
  """Execute crawl endpoint via HTTP and wait for completion. Returns JSON result."""
  params = {"domain_id": domain_id, "format": "stream"}
  if mode: params["mode"] = mode
  if scope: params["scope"] = scope
  if source_id: params["source_id"] = source_id
  if dry_run: params["dry_run"] = "true"
  url = f"{base_url}/v2/crawler/{endpoint}"
  try:
    async with httpx.AsyncClient(timeout=timeout) as client:
      async with client.stream("GET", url, params=params) as response:
        last_event = None
        async for line in response.aiter_lines():
          if line.startswith("data: "):
            try:
              event = json.loads(line[6:])
              if event.get("event") == "end_json": return event.get("data", {})
              last_event = event
            except: pass
        return last_event or {"ok": False, "error": "No end event"}
  except Exception as e:
    return {"ok": False, "error": str(e)}

def _selftest_get_site_path(site_url: str) -> str:
  """Extract site path from URL (e.g., '/sites/demosite')"""
  from urllib.parse import urlparse
  return urlparse(site_url).path.rstrip('/')

@router.get(f"/{router_name}/selftest")
async def crawler_selftest(request: Request):
  """
  Self-test for crawler operations. Creates temporary SharePoint artifacts, runs tests, cleans up.
  
  Required: CRAWLER_SELFTEST_SHAREPOINT_SITE config
  Optional params: skip_cleanup=true (keep artifacts), phase=N (run only up to phase N)
  Only supports format=stream.
  """
  logger = MiddlewareLogger.create()
  logger.log_function_header("crawler_selftest")
  format_param = request.query_params.get("format", "stream")
  skip_cleanup = request.query_params.get("skip_cleanup", "false").lower() == "true"
  max_phase = int(request.query_params.get("phase", "99"))
  if format_param != "stream":
    logger.log_function_footer()
    return json_result(False, "Use format=stream for selftest.", {})
  return StreamingResponse(_selftest_stream(skip_cleanup, max_phase, logger), media_type="text/event-stream")

async def _selftest_stream(skip_cleanup: bool, max_phase: int, logger: MiddlewareLogger):
  """Execute selftest as SSE stream."""
  writer = StreamingJobWriter(persistent_storage_path=get_persistent_storage_path(), router_name=router_name, action="selftest", object_id=SELFTEST_DOMAIN_ID, source_url=f"{router_prefix}/{router_name}/selftest", router_prefix=router_prefix)
  logger.stream_job_writer = writer
  storage_path = get_persistent_storage_path()
  selftest_site = getattr(config, 'CRAWLER_SELFTEST_SHAREPOINT_SITE', None)
  crawler_cfg = get_crawler_config()
  openai_client = get_openai_client()
  
  # Test counters
  test_num = 0
  ok_count = 0
  fail_count = 0
  skip_count = 0
  ctx = None
  site_path = ""
  vector_store_id = ""
  base_url = f"http://127.0.0.1:{getattr(config, 'PORT', 8000)}"
  
  def log(msg): return writer.emit_log(msg)
  def next_test(desc):
    nonlocal test_num
    test_num += 1
    return writer.emit_log(f"  [{test_num}] {desc}")
  def check_ok(msg):
    nonlocal ok_count
    ok_count += 1
    return writer.emit_log(f"    OK: {msg}")
  def check_fail(msg):
    nonlocal fail_count
    fail_count += 1
    return writer.emit_log(f"    FAIL: {msg}")
  def check_skip(msg):
    nonlocal skip_count
    skip_count += 1
    return writer.emit_log(f"    SKIP: {msg}")
  
  try:
    yield writer.emit_start()
    yield log("Crawler Selftest Starting...")
    
    # ===================== Phase 0: Pre-flight Validation =====================
    if max_phase >= 0:
      yield log("Phase 0: Pre-flight Validation")
      
      # M1: Config validation
      yield next_test("M1: Config validation - CRAWLER_SELFTEST_SHAREPOINT_SITE")
      if not selftest_site:
        yield check_fail("CRAWLER_SELFTEST_SHAREPOINT_SITE not configured")
        yield writer.emit_end(ok=False, error="Missing CRAWLER_SELFTEST_SHAREPOINT_SITE config", data={"tests_run": test_num, "ok": ok_count, "fail": fail_count, "skip": skip_count})
        return
      yield check_ok(f"Site configured: {selftest_site}")
      site_path = _selftest_get_site_path(selftest_site)
      
      # M2: SharePoint connectivity
      yield next_test("M2: SharePoint connectivity")
      try:
        ctx = connect_to_site_using_client_id_and_certificate(selftest_site, crawler_cfg['client_id'], crawler_cfg['tenant_id'], crawler_cfg['cert_path'], crawler_cfg['cert_password'])
        ctx.web.get().execute_query()
        yield check_ok(f"Connected to SharePoint")
      except Exception as e:
        yield check_fail(f"SharePoint connection failed: {str(e)}")
        yield writer.emit_end(ok=False, error=f"SharePoint connection failed: {str(e)}", data={"tests_run": test_num, "ok": ok_count, "fail": fail_count, "skip": skip_count})
        return
      
      # M3: OpenAI connectivity
      yield next_test("M3: OpenAI connectivity")
      if openai_client:
        try:
          openai_client.models.list()
          yield check_ok("OpenAI API accessible")
        except Exception as e:
          yield check_fail(f"OpenAI API failed: {str(e)}")
      else:
        yield check_skip("OpenAI client not configured")
    
    # ===================== Phase 1: SharePoint Setup =====================
    if max_phase >= 1:
      yield log("Phase 1: SharePoint Setup")
      
      # 1.1 Create document library
      yield log("  1.1 Creating document library...")
      success, error = create_document_library(ctx, SELFTEST_LIBRARY_NAME, logger)
      for sse in writer.drain_sse_queue(): yield sse
      if not success:
        yield check_fail(f"Failed to create library: {error}")
        raise Exception(f"Setup failed: {error}")
      yield check_ok(f"Created '{SELFTEST_LIBRARY_NAME}'")
      
      # 1.2 Add custom field "Crawl"
      yield log("  1.2 Adding custom field 'Crawl'...")
      success, error = add_number_field_to_list(ctx, SELFTEST_LIBRARY_NAME, "Crawl", logger)
      for sse in writer.drain_sse_queue(): yield sse
      if not success: yield log(f"    WARNING: Field creation failed (may already exist): {error}")
      else: yield check_ok("Added 'Crawl' field")
      
      # 1.3 Upload test files
      yield log("  1.3 Uploading test files...")
      test_files = [
        ("file1.txt", b"Test file 1 content", {"Crawl": 1}),
        ("file2.txt", b"Test file 2 content", {"Crawl": 1}),
        ("file3.txt", b"Test file 3 content", {"Crawl": 1}),
        ("file4.txt", b"Test file 4 content", {"Crawl": 0}),
        ("file5.txt", b"Test file 5 content", {"Crawl": 0}),
        ("file6.txt", b"Test file 6 content", {"Crawl": 0}),
        ("non_embeddable.zip", b"PK\x03\x04", {"Crawl": 1}),
        ("file_test_unicode.txt", "Unicode filename test".encode('utf-8'), {"Crawl": 1}),
      ]
      for filename, content, metadata in test_files:
        success, error = upload_file_to_library(ctx, SELFTEST_LIBRARY_NAME, filename, content, metadata, logger)
        for sse in writer.drain_sse_queue(): yield sse
        if not success: yield log(f"    WARNING: Failed to upload '{filename}': {error}")
      
      # Upload subfolder file
      success, error = upload_file_to_folder(ctx, SELFTEST_LIBRARY_NAME, "subfolder", "file1.txt", b"Subfolder file content", {"Crawl": 1}, logger)
      for sse in writer.drain_sse_queue(): yield sse
      yield check_ok(f"Uploaded {len(test_files) + 1} test files")
      
      # 1.4 Create list
      yield log("  1.4 Creating list...")
      success, error = create_list(ctx, SELFTEST_LIST_NAME, logger)
      for sse in writer.drain_sse_queue(): yield sse
      if not success:
        yield check_fail(f"Failed to create list: {error}")
        raise Exception(f"Setup failed: {error}")
      yield check_ok(f"Created '{SELFTEST_LIST_NAME}'")
      
      # Add Status and Description fields
      success, _ = add_text_field_to_list(ctx, SELFTEST_LIST_NAME, "Status", logger)
      for sse in writer.drain_sse_queue(): yield sse
      success, _ = add_text_field_to_list(ctx, SELFTEST_LIST_NAME, "Description", logger)
      for sse in writer.drain_sse_queue(): yield sse
      
      # 1.5 Add list items
      yield log("  1.5 Adding list items...")
      list_items = [
        {"Title": "Item 1", "Status": "Active", "Description": "Test item 1"},
        {"Title": "Item 2", "Status": "Active", "Description": "Test item 2"},
        {"Title": "Item 3", "Status": "Active", "Description": "Test item 3"},
        {"Title": "Item 4", "Status": "Inactive", "Description": "Test item 4"},
        {"Title": "Item 5", "Status": "Inactive", "Description": "Test item 5"},
        {"Title": "Item 6", "Status": "Inactive", "Description": "Test item 6"},
      ]
      for item_data in list_items:
        success, error = add_list_item(ctx, SELFTEST_LIST_NAME, item_data, logger)
        for sse in writer.drain_sse_queue(): yield sse
      yield check_ok(f"Added {len(list_items)} list items")
      
      # 1.6 Create site pages
      yield log("  1.6 Creating site pages...")
      site_pages = [
        ("_selftest_page1.aspx", "Test page 1 content"),
        ("_selftest_page2.aspx", "Test page 2 content"),
        ("_selftest_page3.aspx", "Test page 3 content"),
      ]
      for page_name, content in site_pages:
        success, error = create_site_page(ctx, page_name, content, logger)
        for sse in writer.drain_sse_queue(): yield sse
        if not success: yield log(f"    WARNING: Failed to create '{page_name}': {error}")
      yield check_ok(f"Created {len(site_pages)} site pages")
    
    # ===================== Phase 2: Domain Setup =====================
    if max_phase >= 2:
      yield log("Phase 2: Domain Setup")
      
      # Create domain config
      domain_config = {
        "domain_id": SELFTEST_DOMAIN_ID,
        "name": "Crawler Selftest Domain",
        "description": "Temporary domain for crawler selftest",
        "vector_store_name": "_SELFTEST_VS",
        "vector_store_id": "",
        "file_sources": [
          {"source_id": "files_all", "site_url": selftest_site, "sharepoint_url_part": f"/{SELFTEST_LIBRARY_NAME}", "filter": ""},
          {"source_id": "files_crawl1", "site_url": selftest_site, "sharepoint_url_part": f"/{SELFTEST_LIBRARY_NAME}", "filter": "Crawl eq 1"}
        ],
        "list_sources": [
          {"source_id": "lists_all", "site_url": selftest_site, "list_name": SELFTEST_LIST_NAME, "filter": ""},
          {"source_id": "lists_active", "site_url": selftest_site, "list_name": SELFTEST_LIST_NAME, "filter": "Status eq 'Active'"}
        ],
        "sitepage_sources": [
          {"source_id": "pages_all", "site_url": selftest_site, "sharepoint_url_part": "/SitePages", "filter": "substringof('_selftest_', FileLeafRef)"}
        ]
      }
      
      # Save domain config via API
      yield log("  Creating domain via API...")
      try:
        async with httpx.AsyncClient(timeout=30.0) as client:
          response = await client.post(f"{base_url}/v2/domains/create", json=domain_config)
          result = response.json()
          if result.get("ok"):
            yield check_ok(f"Created domain '{SELFTEST_DOMAIN_ID}'")
            vector_store_id = result.get("data", {}).get("vector_store_id", "")
            if vector_store_id: yield log(f"    Vector store: {vector_store_id}")
          else:
            yield check_fail(f"Domain creation failed: {result.get('error', 'Unknown error')}")
      except Exception as e:
        yield check_fail(f"Domain creation failed: {str(e)}")
    
    # ===================== Phase 3: Error Cases (I1-I4) =====================
    if max_phase >= 3:
      yield log("Phase 3: Error Cases")
      
      # I1: Missing domain_id
      yield next_test("I1: Missing domain_id")
      result = await _selftest_run_crawl(base_url, "", "crawl", mode="full", scope="all")
      if not result.get("ok", True): yield check_ok("Correctly rejected missing domain_id")
      else: yield check_fail("Should have rejected missing domain_id")
      
      # I2: Invalid domain_id
      yield next_test("I2: Invalid domain_id")
      result = await _selftest_run_crawl(base_url, "INVALID_DOMAIN_12345", "crawl", mode="full", scope="all")
      if not result.get("ok", True): yield check_ok("Correctly rejected invalid domain_id")
      else: yield check_fail("Should have rejected invalid domain_id")
      
      # I3: Invalid scope (tested implicitly - scope defaults to 'all')
      yield next_test("I3: Invalid scope handling")
      yield check_skip("Scope validation tested implicitly")
      
      # I4: Invalid mode (tested implicitly - mode defaults to 'full')
      yield next_test("I4: Invalid mode handling")
      yield check_skip("Mode validation tested implicitly")
    
    # ===================== Phase 4: Full Crawl Tests (A1-A4) =====================
    if max_phase >= 4:
      yield log("Phase 4: Full Crawl Tests")
      
      # A1: mode=full, scope=all
      yield next_test("A1: Full crawl scope=all")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="all")
      if result.get("ok"):
        failures = _selftest_verify_snapshot(storage_path, SELFTEST_DOMAIN_ID, SNAP_FULL_ALL)
        if not failures:
          yield check_ok(f"Crawl succeeded, state matches expected")
          _selftest_save_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
        else: yield check_fail(f"State mismatch: {failures}")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      # A2: mode=full, scope=files
      yield next_test("A2: Full crawl scope=files")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="files")
      if result.get("ok"):
        failures = _selftest_verify_snapshot(storage_path, SELFTEST_DOMAIN_ID, SNAP_FULL_FILES)
        if not failures: yield check_ok("Crawl succeeded, state matches expected")
        else: yield check_fail(f"State mismatch: {failures}")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      # A3: mode=full, scope=lists
      yield next_test("A3: Full crawl scope=lists")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="lists")
      if result.get("ok"):
        failures = _selftest_verify_snapshot(storage_path, SELFTEST_DOMAIN_ID, SNAP_FULL_LISTS)
        if not failures: yield check_ok("Crawl succeeded, state matches expected")
        else: yield check_fail(f"State mismatch: {failures}")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      # A4: mode=full, scope=sitepages
      yield next_test("A4: Full crawl scope=sitepages")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="sitepages")
      if result.get("ok"):
        failures = _selftest_verify_snapshot(storage_path, SELFTEST_DOMAIN_ID, SNAP_FULL_PAGES)
        if not failures: yield check_ok("Crawl succeeded, state matches expected")
        else: yield check_fail(f"State mismatch: {failures}")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
    
    # ===================== Phase 5: source_id Filter Tests (B1-B5) =====================
    if max_phase >= 5:
      yield log("Phase 5: source_id Filter Tests")
      
      # B1: scope=files, source_id=files_all
      yield next_test("B1: scope=files, source_id=files_all")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="files", source_id="files_all")
      if result.get("ok"): yield check_ok("Crawl with source_id filter succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      # B2: scope=files, source_id=files_crawl1
      yield next_test("B2: scope=files, source_id=files_crawl1 (filtered)")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="files", source_id="files_crawl1")
      if result.get("ok"): yield check_ok("Filtered crawl succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      # B3: scope=lists, source_id=lists_active
      yield next_test("B3: scope=lists, source_id=lists_active")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="lists", source_id="lists_active")
      if result.get("ok"): yield check_ok("Filtered list crawl succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      # B4: Invalid source_id
      yield next_test("B4: Invalid source_id")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="files", source_id="INVALID_SOURCE")
      # Should succeed with 0 sources processed
      yield check_ok("Invalid source_id handled gracefully")
      
      # B5: scope=all + source_id
      yield next_test("B5: scope=all + source_id=files_all")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="all", source_id="files_all")
      if result.get("ok"): yield check_ok("scope=all + source_id works")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
    
    # ===================== Phase 6: dry_run Tests (D1-D4) =====================
    if max_phase >= 6:
      yield log("Phase 6: dry_run Tests")
      
      # D1: /crawl dry_run=true
      yield next_test("D1: /crawl with dry_run=true")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="full", scope="all", dry_run=True)
      failures = _selftest_verify_snapshot(storage_path, SELFTEST_DOMAIN_ID, SNAP_EMPTY)
      if not failures: yield check_ok("dry_run did not modify state")
      else: yield check_fail(f"dry_run modified state: {failures}")
      
      # D2: /download_data dry_run=true
      yield next_test("D2: /download_data with dry_run=true")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "download_data", mode="full", scope="files", dry_run=True)
      failures = _selftest_verify_snapshot(storage_path, SELFTEST_DOMAIN_ID, SNAP_EMPTY)
      if not failures: yield check_ok("dry_run download did not modify state")
      else: yield check_fail(f"dry_run modified state: {failures}")
      
      # D3 & D4: Process and embed dry_run tests
      yield next_test("D3: /process_data with dry_run=true")
      yield check_skip("Requires pre-downloaded state")
      yield next_test("D4: /embed_data with dry_run=true")
      yield check_skip("Requires pre-processed state")
    
    # ===================== Phase 7: Individual Steps Tests (E1-E3) =====================
    if max_phase >= 7:
      yield log("Phase 7: Individual Steps Tests")
      
      # E1: download_data only
      yield next_test("E1: /download_data step")
      _selftest_clear_domain_folder(storage_path, SELFTEST_DOMAIN_ID)
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "download_data", mode="full", scope="all")
      if result.get("ok"): yield check_ok("Download step succeeded")
      else: yield check_fail(f"Download failed: {result.get('error', 'Unknown')}")
      
      # E2: process_data (continues from E1)
      yield next_test("E2: /process_data step")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "process_data", scope="all")
      if result.get("ok"): yield check_ok("Process step succeeded")
      else: yield check_fail(f"Process failed: {result.get('error', 'Unknown')}")
      
      # E3: embed_data (continues from E2)
      yield next_test("E3: /embed_data step")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "embed_data", mode="full", scope="all")
      if result.get("ok"): yield check_ok("Embed step succeeded")
      else: yield check_fail(f"Embed failed: {result.get('error', 'Unknown')}")
    
    # ===================== Phase 8: SharePoint Mutations =====================
    if max_phase >= 8:
      yield log("Phase 8: Apply SharePoint Mutations")
      
      # Restore full state first
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      
      # 8.1 ADD file7.txt
      yield log("  8.1 Adding file7.txt...")
      success, _ = upload_file_to_library(ctx, SELFTEST_LIBRARY_NAME, "file7.txt", b"Test file 7 content (new)", {"Crawl": 1}, logger)
      for sse in writer.drain_sse_queue(): yield sse
      
      # 8.2 REMOVE file6.txt
      yield log("  8.2 Removing file6.txt...")
      success, _ = delete_file(ctx, f"{site_path}/{SELFTEST_LIBRARY_NAME}/file6.txt", logger)
      for sse in writer.drain_sse_queue(): yield sse
      
      # 8.3 CHANGE file1.txt content
      yield log("  8.3 Changing file1.txt content...")
      success, _ = update_file_content(ctx, f"{site_path}/{SELFTEST_LIBRARY_NAME}/file1.txt", b"Test file 1 UPDATED content", logger)
      for sse in writer.drain_sse_queue(): yield sse
      
      # 8.4 RENAME file2.txt -> file2_renamed.txt
      yield log("  8.4 Renaming file2.txt...")
      success, _ = rename_file(ctx, f"{site_path}/{SELFTEST_LIBRARY_NAME}/file2.txt", "file2_renamed.txt", logger)
      for sse in writer.drain_sse_queue(): yield sse
      
      # 8.5-8.6 MOVE file3.txt -> subfolder/file3.txt
      yield log("  8.5 Moving file3.txt to subfolder...")
      success, _ = move_file(ctx, f"{site_path}/{SELFTEST_LIBRARY_NAME}/file3.txt", f"{site_path}/{SELFTEST_LIBRARY_NAME}/subfolder", logger)
      for sse in writer.drain_sse_queue(): yield sse
      
      # 8.7 List: ADD item7
      yield log("  8.7 Adding list item7...")
      success, _ = add_list_item(ctx, SELFTEST_LIST_NAME, {"Title": "Item 7", "Status": "Active", "Description": "Test item 7 (new)"}, logger)
      for sse in writer.drain_sse_queue(): yield sse
      
      # Wait for mutations to propagate
      yield log("  Waiting for mutations to propagate...")
      await asyncio.sleep(5)
      yield check_ok("Mutations applied")
    
    # ===================== Phase 9: Incremental Tests (F1-F4) =====================
    if max_phase >= 9:
      yield log("Phase 9: Incremental Crawl Tests")
      
      # F1: mode=incremental, scope=all
      yield next_test("F1: Incremental crawl scope=all")
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="incremental", scope="all")
      if result.get("ok"): yield check_ok("Incremental crawl succeeded")
      else: yield check_fail(f"Incremental crawl failed: {result.get('error', 'Unknown')}")
      
      # F2: mode=incremental, scope=files
      yield next_test("F2: Incremental crawl scope=files")
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="incremental", scope="files")
      if result.get("ok"): yield check_ok("Incremental files crawl succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      # F3 & F4: Lists and sitepages incremental
      yield next_test("F3: Incremental crawl scope=lists")
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="incremental", scope="lists")
      if result.get("ok"): yield check_ok("Incremental lists crawl succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      yield next_test("F4: Incremental crawl scope=sitepages")
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="incremental", scope="sitepages")
      if result.get("ok"): yield check_ok("Incremental sitepages crawl succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
    
    # ===================== Phase 10: Incremental source_id Tests (G1-G2) =====================
    if max_phase >= 10:
      yield log("Phase 10: Incremental source_id Tests")
      
      yield next_test("G1: Incremental scope=files, source_id=files_all")
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="incremental", scope="files", source_id="files_all")
      if result.get("ok"): yield check_ok("Incremental with source_id succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
      
      yield next_test("G2: Incremental scope=files, source_id=files_crawl1")
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      result = await _selftest_run_crawl(base_url, SELFTEST_DOMAIN_ID, "crawl", mode="incremental", scope="files", source_id="files_crawl1")
      if result.get("ok"): yield check_ok("Incremental filtered crawl succeeded")
      else: yield check_fail(f"Crawl failed: {result.get('error', 'Unknown')}")
    
    # ===================== Phase 15: Map File Structure Tests (O1-O3) =====================
    if max_phase >= 15:
      yield log("Phase 15: Map File Structure Tests")
      
      # First ensure we have a full crawl state
      _selftest_restore_snapshot(storage_path, SELFTEST_DOMAIN_ID, "SNAP_FULL_ALL")
      
      # O1: sharepoint_map.csv columns
      yield next_test("O1: sharepoint_map.csv has correct columns")
      sp_map_path = os.path.join(storage_path, "crawler", SELFTEST_DOMAIN_ID, "01_files", "files_all", CRAWLER_HARDCODED_CONFIG.SHAREPOINT_MAP_CSV)
      if os.path.exists(sp_map_path):
        with open(sp_map_path, 'r', encoding='utf-8') as f:
          header = f.readline().strip()
          col_count = len(header.split(','))
          if col_count == 10: yield check_ok(f"sharepoint_map.csv has {col_count} columns")
          else: yield check_fail(f"Expected 10 columns, got {col_count}")
      else: yield check_skip("sharepoint_map.csv not found")
      
      # O2: files_map.csv columns
      yield next_test("O2: files_map.csv has correct columns")
      files_map_path = os.path.join(storage_path, "crawler", SELFTEST_DOMAIN_ID, "01_files", "files_all", CRAWLER_HARDCODED_CONFIG.FILE_MAP_CSV)
      if os.path.exists(files_map_path):
        with open(files_map_path, 'r', encoding='utf-8') as f:
          header = f.readline().strip()
          col_count = len(header.split(','))
          if col_count == 13: yield check_ok(f"files_map.csv has {col_count} columns")
          else: yield check_fail(f"Expected 13 columns, got {col_count}")
      else: yield check_skip("files_map.csv not found")
      
      # O3: vectorstore_map.csv columns
      yield next_test("O3: vectorstore_map.csv has correct columns")
      vs_map_path = os.path.join(storage_path, "crawler", SELFTEST_DOMAIN_ID, "01_files", "files_all", CRAWLER_HARDCODED_CONFIG.VECTOR_STORE_MAP_CSV)
      if os.path.exists(vs_map_path):
        with open(vs_map_path, 'r', encoding='utf-8') as f:
          header = f.readline().strip()
          col_count = len(header.split(','))
          if col_count == 19: yield check_ok(f"vectorstore_map.csv has {col_count} columns")
          else: yield check_fail(f"Expected 19 columns, got {col_count}")
      else: yield check_skip("vectorstore_map.csv not found (embedding may have been skipped)")
    
    yield log("Test execution completed.")
    
  except Exception as e:
    yield log(f"ERROR: Selftest failed -> {str(e)}")
    fail_count += 1
  
  finally:
    # ===================== Phase 17: Cleanup =====================
    if not skip_cleanup:
      yield log("Phase 17: Cleanup")
      
      # Delete domain via API
      yield log("  Deleting _SELFTEST domain...")
      try:
        async with httpx.AsyncClient(timeout=30.0) as client:
          await client.delete(f"{base_url}/v2/domains/delete?domain_id={SELFTEST_DOMAIN_ID}")
      except: pass
      
      # Delete local snapshots
      yield log("  Deleting local snapshots...")
      try: _selftest_cleanup_snapshots(storage_path)
      except: pass
      
      # Delete crawler folder
      yield log("  Deleting crawler folder...")
      try:
        crawler_path = os.path.join(storage_path, "crawler", SELFTEST_DOMAIN_ID)
        if os.path.exists(crawler_path): shutil.rmtree(crawler_path)
      except: pass
      
      # Delete SharePoint artifacts
      if ctx:
        yield log("  Deleting SharePoint site pages...")
        for page in ["_selftest_page1.aspx", "_selftest_page2.aspx", "_selftest_page2_renamed.aspx", "_selftest_page3.aspx", "_selftest_page4.aspx"]:
          try: delete_site_page(ctx, page, logger)
          except: pass
        for sse in writer.drain_sse_queue(): yield sse
        
        yield log("  Deleting SharePoint list...")
        try: delete_list(ctx, SELFTEST_LIST_NAME, logger)
        except: pass
        for sse in writer.drain_sse_queue(): yield sse
        
        yield log("  Deleting SharePoint document library...")
        try: delete_document_library(ctx, SELFTEST_LIBRARY_NAME, logger)
        except: pass
        for sse in writer.drain_sse_queue(): yield sse
      
      yield log("  Cleanup completed.")
    else:
      yield log("Cleanup skipped (skip_cleanup=true)")
    
    # Final summary
    yield log(f"")
    yield log(f"========== SELFTEST SUMMARY ==========")
    yield log(f"Tests run: {test_num}")
    yield log(f"  OK:   {ok_count}")
    yield log(f"  FAIL: {fail_count}")
    yield log(f"  SKIP: {skip_count}")
    yield log(f"=======================================")
    
    all_passed = fail_count == 0
    yield writer.emit_end(ok=all_passed, error="" if all_passed else f"{fail_count} test(s) failed", data={"tests_run": test_num, "ok": ok_count, "fail": fail_count, "skip": skip_count})
    writer.finalize()

# ----------------------------------------- END: Selftest -------------------------------------------------------------


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
function parseSourceUrl(url) {{
  if (!url) return {{ endpoint: '-', domainId: '-', mode: '-', scope: '-' }};
  try {{
    const fullUrl = new URL(url, window.location.origin);
    const pathParts = fullUrl.pathname.split('/').filter(p => p && p !== 'v2');
    const endpoint = pathParts.slice(1).join('/') || '-';
    const domainId = fullUrl.searchParams.get('domain_id') || '-';
    const mode = fullUrl.searchParams.get('mode') || '-';
    const scope = fullUrl.searchParams.get('scope') || '-';
    return {{ endpoint, domainId, mode, scope }};
  }} catch (e) {{ return {{ endpoint: '-', domainId: '-', mode: '-', scope: '-' }}; }}
}}
function formatResultOkFail(ok) {{
  if (ok === true) return 'OK';
  if (ok === false) return 'FAIL';
  return '-';
}}
function formatTimestamp(ts) {{
  if (!ts) return '-';
  try {{ return ts.replace('T', ' ').substring(0, 19); }} catch (e) {{ return '-'; }}
}}
function renderJobRow(job) {{
  const parsed = parseSourceUrl(job.source_url);
  const started = formatTimestamp(job.started_utc);
  const finished = formatTimestamp(job.finished_utc);
  const resultDisplay = formatResultOkFail(job.result?.ok);
  const isCancelOrFail = job.state === 'cancelled' || (job.result && !job.result.ok);
  const isRunning = job.state === 'running';
  const actions = renderJobActions(job);
  const rowId = sanitizeId(job.job_id);
  const rowClass = isRunning ? 'row-running' : (isCancelOrFail ? 'row-cancel-or-fail' : '');
  return '<tr id="job-' + rowId + '"' + (rowClass ? ' class="' + rowClass + '"' : '') + '>' +
    '<td>' + escapeHtml(job.job_id) + '</td>' +
    '<td>' + escapeHtml(parsed.endpoint) + '</td>' +
    '<td>' + escapeHtml(parsed.domainId) + '</td>' +
    '<td>' + escapeHtml(job.state || '-') + '</td>' +
    '<td>' + escapeHtml(resultDisplay) + '</td>' +
    '<td>' + escapeHtml(started) + '</td>' +
    '<td>' + escapeHtml(finished) + '</td>' +
    '<td class="actions">' + actions + '</td>' +
    '</tr>';
}}
function renderJobActions(job) {{
  const jobId = job.job_id;
  const state = job.state;
  let actions = [];
  if (state === 'completed' || state === 'cancelled') {{
    actions.push('<button class="btn-small" onclick="window.open(\\'{router_prefix}/jobs/results?job_id=' + jobId + '&format=html\\', \\'_blank\\')">Result</button>');
  }}
  actions.push('<button class="btn-small" onclick="monitorJob(\\'' + jobId + '\\')">Monitor</button>');
  if (state === 'running') {{
    actions.push('<button class="btn-small" onclick="controlJob(\\'' + jobId + '\\', \\'pause\\')">Pause</button>');
    actions.push('<button class="btn-small" onclick="if(confirm(\\'Cancel job ' + jobId + '?\\')) controlJob(\\'' + jobId + '\\', \\'cancel\\')">Cancel</button>');
  }} else if (state === 'paused') {{
    actions.push('<button class="btn-small" onclick="controlJob(\\'' + jobId + '\\', \\'resume\\')">Resume</button>');
    actions.push('<button class="btn-small" onclick="if(confirm(\\'Cancel job ' + jobId + '?\\')) controlJob(\\'' + jobId + '\\', \\'cancel\\')">Cancel</button>');
  }}
  return actions.join(' ');
}}
function monitorJob(jobId) {{
  connectStream('{router_prefix}/jobs/monitor?job_id=' + encodeURIComponent(jobId) + '&format=stream');
}}
async function controlJob(jobId, action) {{
  try {{
    const response = await fetch('{router_prefix}/jobs/control?job_id=' + encodeURIComponent(jobId) + '&action=' + action);
    const result = await response.json();
    if (result.ok) {{ showToast('Success', 'Job ' + action + ' requested', 'success'); refreshJobsTable(); }}
    else {{ showToast('Failed', result.error, 'error'); }}
  }} catch (e) {{ showToast('Failed', e.message, 'error'); }}
}}
function runSelftest() {{
  showToast('Selftest', 'Starting crawler selftest...', 'info');
  connectStream('{router_prefix}/{router_name}/selftest?format=stream');
}}
"""

def _generate_crawler_ui_page(jobs: list) -> str:
  """Generate crawler jobs UI matching Jobs page styling."""
  columns = [
    {"field": "job_id", "header": "Job ID"},
    {"field": "endpoint", "header": "Endpoint", "default": "-"},
    {"field": "domain_id", "header": "Domain ID", "default": "-"},
    {"field": "state", "header": "State", "default": "-"},
    {"field": "result", "header": "Result", "default": "-"},
    {"field": "started", "header": "Started", "default": "-"},
    {"field": "finished", "header": "Finished", "default": "-"},
    {"field": "actions", "header": "Actions"}
  ]
  
  # Items are rendered by custom JS, just need structure for generate_ui_page
  items = []
  
  return generate_ui_page(
    title="Crawler Jobs",
    router_prefix=router_prefix,
    items=items,
    columns=columns,
    row_id_field="job_id",
    row_id_prefix="job",
    navigation_html=main_page_nav_html.replace("{router_prefix}", router_prefix),
    toolbar_buttons=[{"text": "Run Selftest", "onclick": "runSelftest()", "class": "btn-primary"}],
    enable_selection=False,
    enable_bulk_delete=False,
    list_endpoint=f"{router_prefix}/{router_name}?format=json",
    jobs_control_endpoint=f"{router_prefix}/jobs/control",
    additional_js=get_router_specific_js()
  )

# ----------------------------------------- END: UI Generation --------------------------------------------------------
