# INFO: SharePoint REST API - Social / Following

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for Social Following REST API endpoints with request/response JSON
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Follow/unfollow people, documents, sites, and tags
- Get followed content for current user
- Get followers and following counts
- Get follow suggestions

**Key findings**:
- SocialRestFollowingManager (`social.following`) is primary API [VERIFIED]
- ActorType enum: 0=User, 1=Document, 2=Site, 3=Tag [VERIFIED]
- Follow result: 0=OK, 1=AlreadyFollowing, 2=LimitReached, 3=InternalError [VERIFIED]
- Types parameter uses bitmask: 1=Users, 2=Documents, 4=Sites, 8=Tags [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 11 social/following endpoints

- `POST /_api/social.following/follow` - Follow actor
- `POST /_api/social.following/stopfollowing` - Unfollow actor
- `POST /_api/social.following/isfollowed` - Check if following
- `GET /_api/social.following/my` - Get current user info
- `GET /_api/social.following/my/followed(types={n})` - Get followed content
- `GET /_api/social.following/my/followedcount(types={n})` - Get followed count
- `GET /_api/social.following/my/followers` - Get my followers
- `GET /_api/social.following/my/suggestions` - Get follow suggestions
- `GET /_api/social.following/my/followeddocumentsuri` - Get followed docs URL
- `GET /_api/social.following/my/followedsitesuri` - Get followed sites URL

**Permissions required**:
- Application: `Sites.Read.All` (read), `Sites.ReadWrite.All` (follow/unfollow)
- Delegated: `Sites.Read.All` (read), `Sites.ReadWrite.All` (follow/unfollow)

## ActorType Enumeration [VERIFIED]

- **0** - User
- **1** - Document
- **2** - Site
- **3** - Tag

## Types Bitmask [VERIFIED]

Used with `followed` and `followedcount` endpoints:

- **1** - Users
- **2** - Documents
- **4** - Sites
- **8** - Tags
- **15** - All (1+2+4+8)
- **14** - All content except users (2+4+8)

## SP.Social.SocialActorInfo [VERIFIED]

### Properties

- **ActorType** (`Edm.Int32`) - Type of actor (0-3)
- **AccountName** (`Edm.String`) - For users (claims format)
- **ContentUri** (`Edm.String`) - For documents/sites
- **TagGuid** (`Edm.Guid`) - For tags
- **Id** (`Edm.String`) - Actor ID (usually null for requests)

## 1. POST /_api/social.following/follow - Follow Actor

### Description [VERIFIED]

Makes current user start following a user, document, site, or tag.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/social.following/follow
```

### Follow a User

```http
POST https://contoso.sharepoint.com/_api/social.following/follow(ActorType=0,AccountName=@v,Id=null)?@v='i%3A0%23.f%7Cmembership%7Cjohn.smith%40contoso.com'
Authorization: Bearer eyJ0eXAi...
X-RequestDigest: 0x1234...
```

Or with request body:

```json
{
  "actor": {
    "__metadata": { "type": "SP.Social.SocialActorInfo" },
    "ActorType": 0,
    "AccountName": "i:0#.f|membership|john.smith@contoso.com",
    "Id": null
  }
}
```

### Follow a Document

```http
POST https://contoso.sharepoint.com/_api/social.following/follow(ActorType=1,ContentUri=@v,Id=null)?@v='https://contoso.sharepoint.com/Shared%20Documents/report.docx'
```

### Follow a Site

```http
POST https://contoso.sharepoint.com/_api/social.following/follow(ActorType=2,ContentUri=@v,Id=null)?@v='https://contoso.sharepoint.com/sites/TeamSite'
```

### Follow a Tag

```http
POST https://contoso.sharepoint.com/_api/social.following/follow(ActorType=3,TagGuid='19a4a484-c1dc-4bc5-8c93-bb96245ce928',Id=null)
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "Follow": 0
  }
}
```

**Follow result codes**:
- **0** - OK (success)
- **1** - AlreadyFollowing
- **2** - LimitReached
- **3** - InternalError

## 2. POST /_api/social.following/stopfollowing - Unfollow Actor

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/social.following/stopfollowing(ActorType={type},ContentUri=@v,Id=null)?@v='{uri}'
```

### Unfollow a Site

```http
POST https://contoso.sharepoint.com/_api/social.following/stopfollowing(ActorType=2,ContentUri=@v,Id=null)?@v='https://contoso.sharepoint.com/sites/TeamSite'
```

### Response

```json
{
  "d": {
    "StopFollowing": null
  }
}
```

## 3. POST /_api/social.following/isfollowed - Check If Following

### Description [VERIFIED]

Checks if current user is following the specified actor.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/social.following/isfollowed(ActorType={type},ContentUri=@v,Id=null)?@v='{uri}'
```

### Response

```json
{
  "d": {
    "IsFollowed": true
  }
}
```

## 4. GET /_api/social.following/my - Get Current User Info

### Description [VERIFIED]

Returns social information about the current user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/social.following/my
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": { "type": "SP.Social.SocialRestActor" },
    "FollowedDocumentsUri": "https://contoso-my.sharepoint.com/personal/user/_layouts/15/MyFollowedContent.aspx",
    "FollowedSitesUri": "https://contoso-my.sharepoint.com/personal/user/_layouts/15/MyFollowedContent.aspx"
  }
}
```

## 5. GET /_api/social.following/my/followed(types={n}) - Get Followed Content

### Description [VERIFIED]

Returns actors that the current user is following.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/social.following/my/followed(types={types_bitmask})
```

### Examples

```http
# Get followed users
GET /_api/social.following/my/followed(types=1)

# Get followed documents
GET /_api/social.following/my/followed(types=2)

# Get followed sites
GET /_api/social.following/my/followed(types=4)

# Get all followed content
GET /_api/social.following/my/followed(types=15)

# Get followed sites and documents
GET /_api/social.following/my/followed(types=6)
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "Followed": {
      "results": [
        {
          "__metadata": { "type": "SP.Social.SocialActor" },
          "AccountName": null,
          "ActorType": 2,
          "ContentUri": "https://contoso.sharepoint.com/sites/TeamSite",
          "Name": "Team Site",
          "Id": "15.abc123..."
        }
      ]
    }
  }
}
```

## 6. GET /_api/social.following/my/followedcount(types={n}) - Get Followed Count

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/social.following/my/followedcount(types={types_bitmask})
```

### Response

```json
{
  "d": {
    "FollowedCount": 42
  }
}
```

## 7. GET /_api/social.following/my/followers - Get My Followers

### Description [VERIFIED]

Returns users who are following the current user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/social.following/my/followers
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "Followers": {
      "results": [
        {
          "__metadata": { "type": "SP.Social.SocialActor" },
          "AccountName": "i:0#.f|membership|follower@contoso.com",
          "ActorType": 0,
          "Name": "Jane Follower"
        }
      ]
    }
  }
}
```

## 8. GET /_api/social.following/my/suggestions - Get Suggestions

### Description [VERIFIED]

Returns suggested people for the current user to follow.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/social.following/my/suggestions
```

## 9. GET /_api/social.following/my/followeddocumentsuri - Followed Docs URL

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/social.following/my/followeddocumentsuri
```

### Response

```json
{
  "d": {
    "FollowedDocumentsUri": "https://contoso-my.sharepoint.com/personal/user/_layouts/15/MyFollowedContent.aspx"
  }
}
```

## 10. GET /_api/social.following/my/followedsitesuri - Followed Sites URL

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/social.following/my/followedsitesuri
```

## 11. Additional PeopleManager Endpoints

Some social endpoints also available via PeopleManager:

### Get People Followed By

```http
GET /_api/sp.userprofiles.peoplemanager/getpeoplefollowedby(@v)?@v='{account}'
```

### Get Followers For

```http
GET /_api/sp.userprofiles.peoplemanager/getfollowersfor(@v)?@v='{account}'
```

### Am I Followed By

```http
GET /_api/sp.userprofiles.peoplemanager/amifollowedby(@v)?@v='{account}'
```

## Error Responses

- **400** - Invalid actor type or parameters
- **401** - Unauthorized
- **403** - Insufficient permissions
- **404** - Actor not found

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com" -Interactive

# No direct PnP cmdlets - use Invoke-PnPSPRestMethod
$followedSites = Invoke-PnPSPRestMethod -Url "/_api/social.following/my/followed(types=4)" -Method Get
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/social";
const sp = spfi(...);

// Get followed sites
const followed = await sp.social.my.followed(4);

// Follow a site
await sp.social.follow({
  ActorType: 2,
  ContentUri: "https://contoso.sharepoint.com/sites/TeamSite"
});

// Check if following
const isFollowing = await sp.social.isFollowed({
  ActorType: 2,
  ContentUri: "https://contoso.sharepoint.com/sites/TeamSite"
});
```

## Sources

- **SPAPI-SOCIAL-SC-01**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/following-people-and-content-rest-api-reference-for-sharepoint
- **SPAPI-SOCIAL-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/follow-content-in-sharepoint

## Document History

**[2026-01-28 20:45]**
- Initial creation with 11 endpoints
- Documented ActorType and Types bitmask enumerations
- Added examples for all actor types
