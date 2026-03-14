# INFO: SharePoint REST API - User Profile

**Doc ID**: SPAPI-IN01
**Goal**: Detailed reference for User Profile (SP.UserProfiles.PeopleManager) endpoints with request/response JSON
**Research Type**: MCPI (exhaustive endpoint detail)
**Timeline**: Created 2026-01-28

**Depends on**:
- `__INFO_SHAREPOINT_API_TOC.md [SPAPI-IN01]` for endpoint inventory

## Summary

**Use cases**:
- Get user profile properties (current user or specific user)
- Access organizational hierarchy (managers, reports, peers)
- Manage people following relationships
- Get profile suggestions and trending tags

**Key findings**:
- PeopleManager is the main resource for profile operations [VERIFIED]
- Account names must be URL-encoded (claims format) [VERIFIED]
- Following operations also available via social.following API [VERIFIED]
- PersonProperties contains core user info and UserProfileProperties collection [VERIFIED]

## Quick Reference Summary

**Endpoints covered**: 12 user profile endpoints

- `GET /_api/sp.userprofiles.peoplemanager/getmyproperties` - Get current user profile
- `GET /_api/sp.userprofiles.peoplemanager/getpropertiesfor(@v)` - Get user profile by account
- `GET /_api/sp.userprofiles.peoplemanager/getuserprofilepropertyfor(@v)` - Get single property
- `GET /_api/sp.userprofiles.peoplemanager/getmyfollowers` - Get my followers
- `GET /_api/sp.userprofiles.peoplemanager/getfollowersfor(@v)` - Get followers for user
- `GET /_api/sp.userprofiles.peoplemanager/getpeoplefollowedby(@v)` - Get people followed
- `POST /_api/sp.userprofiles.peoplemanager/follow(@v)` - Follow a user
- `POST /_api/sp.userprofiles.peoplemanager/stopfollowing(@v)` - Unfollow a user
- `GET /_api/sp.userprofiles.peoplemanager/amifollowing(@v)` - Check if following
- `GET /_api/sp.userprofiles.peoplemanager/getmysuggestions` - Get follow suggestions
- `GET /_api/sp.userprofiles.peoplemanager/gettrendingtags` - Get trending tags

**Permissions required**:
- Application: `User.Read.All` (read profiles)
- Delegated: `User.Read` (own profile), `User.Read.All` (other profiles)

## Account Name Format [VERIFIED]

Account names use claims format and must be URL-encoded:

- **SharePoint Online**: `i:0#.f|membership|user@domain.com`
- **URL Encoded**: `i%3A0%23.f%7Cmembership%7Cuser%40domain.com`

**Alias syntax**: Use `@v` parameter alias for cleaner URLs:
```
/getpropertiesfor(@v)?@v='i%3A0%23.f%7Cmembership%7Cuser%40domain.com'
```

## SP.UserProfiles.PersonProperties [VERIFIED]

### Properties

- **AccountName** (`Edm.String`) - Claims account name
- **DisplayName** (`Edm.String`) - Display name
- **Email** (`Edm.String`) - Email address
- **Title** (`Edm.String`) - Job title
- **PictureUrl** (`Edm.String`) - Profile picture URL
- **PersonalUrl** (`Edm.String`) - OneDrive/MySite URL
- **UserUrl** (`Edm.String`) - Profile page URL
- **DirectReports** (`Collection(Edm.String)`) - Direct report account names
- **ExtendedManagers** (`Collection(Edm.String)`) - Manager hierarchy
- **ExtendedReports** (`Collection(Edm.String)`) - Extended reports
- **Peers** (`Collection(Edm.String)`) - Peer account names
- **IsFollowed** (`Edm.Boolean`) - Is followed by current user
- **LatestPost** (`Edm.String`) - Latest microblog post
- **UserProfileProperties** (`Collection(SP.KeyValue)`) - All profile properties

## 1. GET /getmyproperties - Get Current User Profile

### Description [VERIFIED]

Returns profile properties for the current user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getmyproperties
```

### Request Example

```http
GET https://contoso.sharepoint.com/_api/sp.userprofiles.peoplemanager/getmyproperties
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "__metadata": {
      "type": "SP.UserProfiles.PersonProperties"
    },
    "AccountName": "i:0#.f|membership|john.smith@contoso.com",
    "DisplayName": "John Smith",
    "Email": "john.smith@contoso.com",
    "Title": "Software Engineer",
    "PictureUrl": "https://contoso-my.sharepoint.com/User Photos/Profile Pictures/john_smith_contoso_com_MThumb.jpg",
    "PersonalUrl": "https://contoso-my.sharepoint.com/personal/john_smith_contoso_com/",
    "UserUrl": "https://contoso-my.sharepoint.com/Person.aspx?accountname=i%3A0%23%2Ef%7Cmembership%7Cjohn%2Esmith%40contoso%2Ecom",
    "DirectReports": { "results": [] },
    "ExtendedManagers": { "results": ["i:0#.f|membership|manager@contoso.com"] },
    "Peers": { "results": [] },
    "IsFollowed": false,
    "UserProfileProperties": {
      "results": [
        { "Key": "Department", "Value": "Engineering", "ValueType": "Edm.String" },
        { "Key": "SPS-Location", "Value": "Seattle", "ValueType": "Edm.String" },
        { "Key": "Manager", "Value": "i:0#.f|membership|manager@contoso.com", "ValueType": "Edm.String" }
      ]
    }
  }
}
```

## 2. GET /getpropertiesfor(@v) - Get User Profile by Account

### Description [VERIFIED]

Returns profile properties for a specified user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getpropertiesfor(@v)?@v='{encoded_account}'
```

### Request Example

```http
GET https://contoso.sharepoint.com/_api/sp.userprofiles.peoplemanager/getpropertiesfor(@v)?@v='i%3A0%23.f%7Cmembership%7Cjane.doe%40contoso.com'
Authorization: Bearer eyJ0eXAi...
Accept: application/json;odata=verbose
```

## 3. GET /getuserprofilepropertyfor(@v) - Get Single Property

### Description [VERIFIED]

Returns a single profile property for a specified user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getuserprofilepropertyfor(accountname=@v,propertyname='{property}')?@v='{encoded_account}'
```

### Request Example

```http
GET https://contoso.sharepoint.com/_api/sp.userprofiles.peoplemanager/getuserprofilepropertyfor(accountname=@v,propertyname='Department')?@v='i%3A0%23.f%7Cmembership%7Cjohn.smith%40contoso.com'
```

### Response

```json
{
  "d": {
    "GetUserProfilePropertyFor": "Engineering"
  }
}
```

## 4. GET /getmyfollowers - Get My Followers

### Description [VERIFIED]

Returns people following the current user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getmyfollowers
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "results": [
      {
        "__metadata": { "type": "SP.UserProfiles.PersonProperties" },
        "AccountName": "i:0#.f|membership|follower@contoso.com",
        "DisplayName": "Jane Follower",
        "Email": "follower@contoso.com"
      }
    ]
  }
}
```

## 5. GET /getfollowersfor(@v) - Get Followers for User

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getfollowersfor(@v)?@v='{encoded_account}'
```

## 6. GET /getpeoplefollowedby(@v) - Get People Followed

### Description [VERIFIED]

Returns people that the specified user is following.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getpeoplefollowedby(@v)?@v='{encoded_account}'
```

## 7. GET /getpeoplefollowedbyMe - Get People I Follow

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getpeoplefollowedbyMe
```

## 8. POST /follow(@v) - Follow a User

### Description [VERIFIED]

Adds specified user to current user's followed people list.

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/follow(@v)?@v='{encoded_account}'
```

### Request Example

```http
POST https://contoso.sharepoint.com/_api/sp.userprofiles.peoplemanager/follow(@v)?@v='i%3A0%23.f%7Cmembership%7Cjane.doe%40contoso.com'
Authorization: Bearer eyJ0eXAi...
X-RequestDigest: 0x1234...
```

## 9. POST /stopfollowing(@v) - Unfollow a User

### HTTP Request

```http
POST https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/stopfollowing(@v)?@v='{encoded_account}'
```

## 10. GET /amifollowing(@v) - Check If Following

### Description [VERIFIED]

Checks if current user is following the specified user.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/amifollowing(@v)?@v='{encoded_account}'
```

### Response

```json
{
  "d": {
    "AmIFollowing": true
  }
}
```

## 11. GET /amifollowedby(@v) - Check If Followed By

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/amifollowedby(@v)?@v='{encoded_account}'
```

## 12. GET /getmysuggestions - Get Follow Suggestions

### Description [VERIFIED]

Returns suggested people for the current user to follow.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/getmysuggestions
```

## 13. GET /gettrendingtags - Get Trending Tags

### Description [VERIFIED]

Returns trending hashtags.

### HTTP Request

```http
GET https://{tenant}.sharepoint.com/_api/sp.userprofiles.peoplemanager/gettrendingtags
```

### Response JSON [VERIFIED]

```json
{
  "d": {
    "GetTrendingTags": {
      "Items": {
        "results": [
          {
            "Name": "L0|#03e324ad0-de47-4c0a-b9c6-59fda8419430|#sharepoint",
            "UseCount": 150
          }
        ]
      }
    }
  }
}
```

## Common Profile Properties [VERIFIED]

- **PreferredName** - Display name
- **Department** - Department
- **Title** - Job title
- **Manager** - Manager account name
- **SPS-Location** - Office location
- **SPS-Skills** - Skills (multi-value)
- **SPS-Interests** - Interests (multi-value)
- **SPS-School** - Schools attended
- **SPS-Birthday** - Birthday
- **SPS-HireDate** - Hire date
- **SPS-JobTitle** - Job title
- **SPS-Department** - Department
- **WorkPhone** - Work phone
- **CellPhone** - Mobile phone
- **Office** - Office location
- **AboutMe** - About me text
- **PictureURL** - Profile picture URL
- **PersonalSpace** - OneDrive URL

## Error Responses

- **400** - Invalid account name format
- **401** - Unauthorized
- **403** - Forbidden (privacy settings)
- **404** - User not found

## SDK Examples

**PnP PowerShell**:
```powershell
Connect-PnPOnline -Url "https://contoso.sharepoint.com" -Interactive
Get-PnPUserProfileProperty -Account "john.smith@contoso.com"
Get-PnPUserProfileProperty -Account "i:0#.f|membership|john.smith@contoso.com"
```

**PnP JavaScript** (v4.x):
```javascript
import { spfi } from "@pnp/sp";
import "@pnp/sp/profiles";
const sp = spfi(...);

const myProfile = await sp.profiles.myProperties();
const userProfile = await sp.profiles.getPropertiesFor("i:0#.f|membership|user@contoso.com");
const dept = await sp.profiles.getUserProfilePropertyFor("i:0#.f|membership|user@contoso.com", "Department");
```

## Sources

- **SPAPI-PROFILE-SC-01**: https://learn.microsoft.com/en-us/previous-versions/office/developer/sharepoint-rest-reference/dn790354(v=office.15)
- **SPAPI-PROFILE-SC-02**: https://learn.microsoft.com/en-us/sharepoint/dev/general-development/work-with-user-profiles-in-sharepoint

## Document History

**[2026-01-28 20:05]**
- Initial creation with 12 endpoints
- Documented PersonProperties structure
- Added common profile property names
