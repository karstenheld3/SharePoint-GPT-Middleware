# Mastering SharePoint Permissions

**Source**: MasteringSharePointPermissions.pdf (55 pages)
**Transcribed**: 2026-01-28

---

<!-- PAGE 1 -->

# SharePoint Tips & Tricks

## Mastering SharePoint Permissions

Karsten Held, April 2020

<!-- Decorative: logo, raccoon graphic -->

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 2 -->

# What we will cover

- How do SharePoint permissions work  
- Where to find the permission settings  
- What are permission levels  
- How to add people to SharePoint groups  
- How does individual sharing change permissions  
- Tips & Tricks for SharePoint permissions  
- Other groups in Office 356  

<transcription_page_footer> Page [unclear] | Vattenfall </transcription_page_footer>

---

<!-- PAGE 3 -->

# Mastering SharePoint Permissions

## How do SharePoint permissions work

<transcription_image>
**Figure 1: Illustration of a puzzled raccoon character with a question mark on its chest**

```ascii
       [RACCOON CHARACTER]
     +---------------------+
     |   __   __           |
     |  |__| |__|  [EYES]  |
     |   [MASK]           |
     |    [???]           |
     |   [QUESTION MARK]  |
     +---------------------+

Legend:
[RACCOON CHARACTER] = cartoon raccoon with question mark on torso
[QUESTION MARK] = blue question mark symbol
[EYES] = white eyes with black pupils
[MASK] = grey mask around eyes
```

<transcription_notes>
- Colors: 
  - Blue = question mark symbol on chest
  - Grey = raccoon body and mask
  - Pink = inside ears and tongue
  - Green = small patch beneath raccoon (ground)
  - Light blue circle around raccoon (border)
- No numeric data present
- ASCII misses: detailed pixel art, shading, and color gradients
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 4 -->

# How SharePoint permissions work

## Permission structure overview

<transcription_image>
**Figure 1: How SharePoint permissions work**

```ascii
HOW SHAREPOINT PERMISSIONS WORK

Site Objects          Permission Levels          Groups                Users
+------------+        +--------------+           +-----------+         (User) (User)
|  Site      | <----  | Full Control | <-------  |  Owner    | <----  (User) (User) (User) (User)
+------------+        +--------------+           +-----------+
     ^                      ^                         ^
     |                      |                         |
     |                      |                         |
     |                      |                         |
     v                      v                         v
+--------------+        +-------+              +-----------+         (User) (User) (User) (User)
| List /       | <----  | Edit  | <-------  |  Member   | <----  (User) (User)
| Library      |        +-------+              +-----------+
+--------------+                                    ^
     ^                                             |
     |                                             |
     |                                             |
     v                                             v
+------------+        +-------+              +-----------+         (User)
| Folder     | <----  | Read  | <-------  |  Visitors | <----  (User)
+------------+        +-------+              +-----------+
     ^
     |
     |
     v
+--------------+
| Item / File  |
+--------------+

Arrows labeled:
- "define object permissions" from Site Objects to Permission Levels
- "have permission level" from Permission Levels to Groups
- "belong to groups" from Groups to Users

Arrows labeled:
- "inherits from" from Site to List/Library
- "inherits from" from List/Library to Folder
- "inherits from" from Folder to Item/File
```

<transcription_notes>
- Data: No numeric data.
- Colors: Blue boxes for Site Objects and Permission Levels; outlined rounded boxes for Groups; user icons for Users.
- ASCII misses: User icons represented as (User).
</transcription_notes>
</transcription_image>

---

<!-- PAGE 5 -->

```markdown
# Mastering SharePoint Permissions

## Where to find the permission settings

<!-- Decorative: character illustration, Vattenfall logo -->

<transcription_page_footer> Page 1 | Vattenfall </transcription_page_footer>
```


---

<!-- PAGE 6 -->

# How to find Groups and Permission Levels

<transcription_image>
**Figure 1: Navigation steps and interface for finding SharePoint groups and permission levels**

```ascii
[My SharePoint Site Interface]

+-------------------------------------------------------------+
| [1] Site Contents                                           |
|  Home                                                      |
|  Find File & Folders                                       |
|  Documents                                                 |
|  Site Contents  <--- [1]                                  |
|  Movies                                                    |
|  Movies2                                                   |
|  Edit                                                      |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
| Top menu bar:                                               |
| ... Site usage | Site workflows | [2] Site settings | ...   |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
| Site Settings page                                         |
| Users and Permissions                                      |
| [3] Site permissions  <---                                |
+-------------------------------------------------------------+

+-------------------------------------------------------------+
| [Permissions Tab]                                          |
| [Permission Levels]  <--- [Edit Permission Levels]        |
+-------------------------------------------------------------+

+------------------------------------+-----------------------+-----------------------+
| Name                               | Type                  | Permission Levels      |
+------------------------------------+-----------------------+-----------------------+
| Approvers                         | SharePoint Group       | Approve               |
| Designers                        | SharePoint Group       | Design                |
| Excel Services Viewers            | SharePoint Group       | View Only             |
| Hierarchy Managers                | SharePoint Group       | Manage Hierarchy      |
| Restricted Readers               | SharePoint Group       | Restricted Read       |
| SharePoint SupportTest Members   | SharePoint Group       | Edit                  |
| SharePoint SupportTest Owners    | SharePoint Group       | Full Control          |
| SharePoint SupportTest Visitors  | SharePoint Group       | Read                  |
| Translation Managers             | SharePoint Group       | Restricted Interfaces for Translation |
+------------------------------------+-----------------------+-----------------------+

Legend:
[1] = Site Contents menu item
[2] = Site settings button in top menu
[3] = Site permissions link in Site Settings page
[Edit Permission Levels] = Button/tab to edit permissions
Groups = Left column under "Name"
Permission Levels = Right column under "Permission Levels"
```

<transcription_notes>
- Data: List of groups and their permission levels exactly as shown.
- Navigation steps labeled with [1], [2], [3].
- The main focus is on how to navigate from "Site Contents" to "Site Settings" to "Site permissions" and then to edit permission levels.
- Colors: Red boxes and arrows highlight key UI elements and labels (not transcribed in ASCII).
- Some UI elements like icons and minor text are omitted due to ASCII limitations.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 7 -->

# How to find the permissions of a library

<transcription_image>
**Figure 1: Steps to find the permissions of a library in SharePoint**

```ascii
+------------------------------------------------------------+
| [PROCESS 1]                                                |
|  Click Settings gear icon ⚙️                                |
|  [Label 1]                                                 |
+------------------------------------------------------------+
              |
              v
+------------------------------------------------------------+
| [PROCESS 2]                                                |
|  Select "Library settings"                                  |
|  [Label 2]                                                 |
+------------------------------------------------------------+
              |
              v
+------------------------------------------------------------+
| [PROCESS 3]                                                |
|  Under Permissions and Management:                         |
|  Click "Permissions for this document library"             |
|  [Label 3]                                                 |
+------------------------------------------------------------+
```

Legend: [PROCESS 1]=Open Settings, [PROCESS 2]=Open Library settings, [PROCESS 3]=Access permissions

<transcription_notes>
- Data: Steps labeled 1, 2, 3 indicating the order of actions
- Screenshots show SharePoint UI with highlighted Settings gear icon, "Library settings" link, and "Permissions for this document library" link
- Exact URLs and text shown:
  - Web Address: https://vattenfall.sharepoint.com/sites/spst/Shared Documents/Forms/AllItems.aspx
  - Section headers: General Settings, Permissions and Management, Communications
  - Other links visible but not highlighted: List name, description and navigation, Versioning settings, Advanced settings, Delete this document library, Save document library as template, RSS settings
- Colors: Red boxes highlight steps 1, 2, and 3
- No ASCII misses
</transcription_notes>
</transcription_image>

<transcription_page_footer> Page 1 | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 8 -->

# How to find the permissions of a file or folder

<transcription_image>
**Figure 1: Steps to find permissions of a file or folder in SharePoint**

```ascii
[My SharePoint Site - Documents View]

+-------------------------------------------------------+
| [MS] My SharePoint Site                                |
| Projects                                              |
+-------------------------------------------------------+
| Search | Share | Copy link | Download | Delete | ...  |
+-------------------------------------------------------+
| Home                                                |
| Find File & Folders                                 |
| Documents  <---- Selected folder highlighted       |
| Site Contents                                      |
| Movies                                            |
| Movies2                                           |
| Edit                                              |
+-------------------------------------------------------+

[Documents List]
  - Folder   [1] ... [2] Manage access option selected
  - Book.xlsx
  - Master.xlsx

[Manage Access Panel for Folder]

Manage Access
-------------------------------------------------------
Links Giving Access
  There are no sharing links for this item.

Direct Access
  [SO] SharePoint SupportTest Owners      Owner
  [SV] SharePoint SupportTest Visitors    [unclear: text truncated]
  [SM] SharePoint SupportTest Members     [pencil icon]
  [D ] Designers                          [pencil icon]
  [HM] Hierarchy Managers                 Owner
  [A ] Approvers                         [pencil icon]
  [RR] Restricted Readers                [eye icon]

[3] Advanced (link at bottom right)
```

<transcription_notes>
- Numbered steps highlighted in red circles: 1 = click "..." menu, 2 = select "Manage access", 3 = click "Advanced"
- SharePoint interface elements transcribed exactly as visible
- User/group names and roles listed under "Direct Access" section
- Some text truncated or partially visible (e.g. SharePoint SupportTest Visitors)
- Icons represented descriptively (pencil for edit, eye for view)
</transcription_notes>
</transcription_image>

<transcription_page_footer> Page 1 | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 9 -->

# Mastering SharePoint Permissions

## What are permission levels

<transcription_image>
**Figure 1: Raccoon character with question mark on chest**

```ascii
  +---------------------+
  |      [RACCOON]      |
  |   .--.   .--.       |
  |  |o_o | | o_o|      |
  |  |:_/  | | :_/|      |
  |  //    | | // |      |
  | (|     | | | )|      |
  |/'\_   _/`\'\/       |
  |     '?' on chest     |
  +---------------------+
```

<transcription_notes>
- Graphic of raccoon character with blue question mark on chest.
- Colors: Gray raccoon with pink ears and black stripes on tail, blue question mark.
- No data values.
- Decorative, no ASCII misses.
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 10 -->

# SharePoint Permission Levels

## SharePoint Permission Levels Overview

| Permission Level                  | Description                                                                                              | Risk Level | Summary Description                                |
|---------------------------------|----------------------------------------------------------------------------------------------------------|------------|----------------------------------------------------|
| **Full Control**                 | Has full control.                                                                                        | High (red) | Has all available permissions                      |
| **Design**                      | Can view, add, update, delete, approve, and customize.                                                  | High (red) | Full Control without subsites, groups              |
| **Edit**                        | Can add, edit and delete lists; can view, add, update and delete list items and documents.              | Medium (blue) | Full Control without subsites, groups, site settings |
| **Contribute**                  | Can view, add, update, and delete list items and documents.                                             | Medium (blue) | Edit without list / library settings                |
| **Read**                       | Can view pages and list items and download documents.                                                   | Low (grey) | Read site content                                  |
| **View Only**                  | Can view pages, list items, and documents. Document types with server-side file handlers can be viewed in the browser but not downloaded. | Low (grey) | Read site content without download                 |
| **Approve**                    | Can edit and approve pages, list items, and documents.                                                 | Medium (blue) | Edit and approval without list / library settings  |
| **Manage Hierarchy**           | Can create sites and edit pages, list items, and documents.                                            | High (red) | Full Control without theming, approval              |
| **Restricted Read**            | Can view pages and documents, but cannot view historical versions or user permissions.                  | Low (grey) | Read without alerts                                |
| **Restricted Interfaces for Translation** | Can open lists and folders, and use remote interfaces.                                               | Low (grey) | Read without files, items, pages, alerts           |

---

<transcription_image>
**Figure 1: SharePoint Permission Levels with Roles and Risk Indicators**

```ascii
[OWNERS] --> [ ] Full Control                | Has full control.                                | [High]  | Has all available permissions
           --> [ ] Design                      | Can view, add, update, delete, approve, customize | [High]  | Full Control without subsites, groups

[MEMBERS] --> [ ] Edit                        | Can add, edit and delete lists; can view, add, update and delete list items and documents. | [Medium] | Full Control without subsites, groups, site settings
            --> [ ] Contribute                 | Can view, add, update, and delete list items and documents. | [Medium] | Edit without list / library settings

[VISITORS] --> [ ] Read                       | Can view pages and list items and download documents. | [Low] | Read site content
             --> [ ] View Only                 | Can view pages, list items, and documents. Document types with server-side file handlers can be viewed in the browser but not downloaded. | [Low] | Read site content without download
             --> [ ] Approve                   | Can edit and approve pages, list items, and documents. | [Medium] | Edit and approval without list / library settings
             --> [ ] Manage Hierarchy          | Can create sites and edit pages, list items, and documents. | [High] | Full Control without theming, approval
             --> [ ] Restricted Read           | Can view pages and documents, but cannot view historical versions or user permissions. | [Low] | Read without alerts
             --> [ ] Restricted Interfaces for Translation | Can open lists and folders, and use remote interfaces. | [Low] | Read without files, items, pages, alerts
```

Legend:
- `[OWNERS]`, `[MEMBERS]`, `[VISITORS]` = User Role Groups
- `[ ]` = Checkbox for selection
- `[High]` = Red risk indicator
- `[Medium]` = Blue risk indicator
- `[Low]` = Grey risk indicator

<transcription_notes>
- Data: Permission levels, descriptions, risk levels (High, Medium, Low), and corresponding summaries.
- Colors: Red = High risk; Blue = Medium risk; Grey = Low risk
- ASCII misses: Exact checkbox positioning and arrow styling simplified; icons for Owners, Members, Visitors replaced with text labels.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 11 -->

# How does a Permission Level look like?

<!-- Column 1 -->

Name:  
Edit

Description:  
Can add, edit and delete lists; can view, add, update and delete list items and documents.

Select the permissions to include in this permission level.  
☐ Select All

## List Permissions

☑ Manage Lists  - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.

☐ Override List Behaviors  - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items

☑ Add Items  - Add items to lists and add documents to document libraries.

☑ Edit Items  - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.

☑ Delete Items  - Delete items from a list and documents from a document library.

☑ View Items  - View items in lists and documents in document libraries.

☐ Approve Items  - Approve a minor version of a list item or document.

☑ Open Items  - View the source of documents with server-side file handlers.

☑ View Versions  - View past versions of a list item or document.

☑ Delete Versions  - Delete past versions of a list item or document.

☑ Create Alerts  - Create alerts.

☑ View Application Pages  - View forms, views, and application pages. Enumerate lists.

<!-- Column 2 -->

## Site Permissions

☐ Manage Permissions  - Create and change permission levels on the Web site and assign permissions to users and groups.

☐ View Web Analytics Data  - View reports on Web site usage.

☐ Create Subsites  - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.

☐ Manage Web Site  - Grants the ability to perform all administration tasks for the Web site as well as manage content.

☐ Add and Customize Pages  - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.

☐ Apply Themes and Borders  - Apply a theme or borders to the entire Web site.

☐ Apply Style Sheets  - Apply a style sheet (.CSS file) to the Web site.

☐ Create Groups  - Create a group of users that can be used anywhere within the site collection.

☑ Browse Directories  - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.

☑ Use Self-Service Site Creation  - Create a Web site using Self-Service Site Creation.

☐ View Pages  - View pages in a Web site.

☐ Enumerate Permissions  - Enumerate permissions on the Web site, list, folder, document, or list item.

☑ Browse User Information  - View information about users of the Web site.

☐ Manage Alerts  - Manage alerts for all users of the Web site.

☑ Use Remote Interfaces  - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.

☑ Use Client Integration Features  - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.

☑ Open  - Allows users to open a Web site, list, or folder in order to access items inside that container.

☑ Edit Personal User Information  - Allows a user to change his or her own user information, such as adding a picture.

<!-- Column 3 -->

## Personal Permissions

☑ Manage Personal Views  - Create, change, and delete personal views of lists.

☑ Add/Remove Personal Web Parts  - Add or remove personal Web Parts on a Web Part Page.

☑ Update Personal Web Parts  - Update Web Parts to display personalized information.

<transcription_page_footer> 11 </transcription_page_footer>

---

<!-- PAGE 12 -->

# Restricted Interfaces for Translation - Can read lists, document libraries, folders but not site, files, items, pages

Name:  
`Restricted Interfaces for Translation`

Description:  
Can open lists and folders, and use remote interfaces.

Select the permissions to include in this permission level.

☐ Select All

## List Permissions

☐ Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.

☐ Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items

☐ Add Items - Add items to lists and add documents to document libraries.

☐ Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.

☐ Delete Items - Delete items from a list and documents from a document library.

☐ View Items - View items in lists and documents in document libraries.

☐ Approve Items - Approve a minor version of a list item or document.

☐ Open Items - View the source of documents with server-side file handlers.

☐ View Versions - View past versions of a list item or document.

☐ Delete Versions - Delete past versions of a list item or document.

☐ Create Alerts - Create alerts.

☐ View Application Pages - View forms, views, and application pages. Enumerate lists.

## Site Permissions

☐ Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.

☐ View Web Analytics Data - View reports on Web site usage.

☐ Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.

☐ Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.

☐ Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.

☐ Apply Themes and Borders - Apply a theme or borders to the entire Web site.

☐ Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.

☐ Create Groups - Create a group of users that can be used anywhere within the site collection.

☐ Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.

☐ Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

☐ View Pages - View pages in a Web site.

☐ Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.

☐ Browse User Information - View information about users of the Web site.

☐ Manage Alerts - Manage alerts for all users of the Web site.

☑ Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.

☐ Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.

☑ Open - Allows users to open a Web site, list, or folder in order to access items inside that container.

☐ Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

## Personal Permissions

☐ Manage Personal Views - Create, change, and delete personal views of lists.

☐ Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.

☐ Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 13 -->

# Restricted Read - Can read site, pages, lists, document libraries, files, items

Name:  
`Restricted Read`

Description:  
Can view pages and documents, but cannot view historical versions or user permissions.

Select the permissions to include in this permission level.

- [ ] Select All

## List Permissions

- [ ] Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.

- [ ] Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items

- [ ] Add Items - Add items to lists and add documents to document libraries.

- [ ] Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.

- [ ] Delete Items - Delete items from a list and documents from a document library.

- [x] View Items - View items in lists and documents in document libraries.

- [ ] Approve Items - Approve a minor version of a list item or document.

- [x] Open Items - View the source of documents with server-side file handlers.

- [ ] View Versions - View past versions of a list item or document.

- [ ] Delete Versions - Delete past versions of a list item or document.

- [ ] Create Alerts - Create alerts.

- [ ] View Application Pages - View forms, views, and application pages. Enumerate lists.

## Site Permissions

- [ ] Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.

- [ ] View Web Analytics Data - View reports on Web site usage.

- [ ] Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.

- [ ] Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.

- [ ] Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.

- [ ] Apply Themes and Borders - Apply a theme or borders to the entire Web site.

- [ ] Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.

- [ ] Create Groups - Create a group of users that can be used anywhere within the site collection.

- [ ] Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.

- [ ] Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

- [x] View Pages - View pages in a Web site.

- [ ] Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.

- [ ] Browse User Information - View information about users of the Web site.

- [ ] Manage Alerts - Manage alerts for all users of the Web site.

- [ ] Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.

- [ ] Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.

- [x] Open - Allows users to open a Web site, list, or folder in order to access items inside that container.

- [ ] Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

## Personal Permissions

- [ ] Manage Personal Views - Create, change, and delete personal views of lists.

- [ ] Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.

- [ ] Update Personal Web Parts - Update Web Parts to display personalized information.

---

<transcription_image>  
**Figure 1: Restricted Read Permission Settings with Highlights**

```ascii
[Restricted Read Permissions]

Name: [Restricted Read]
Description: [Can view pages and documents, but cannot view historical versions or user permissions.]

[List Permissions]
[ ] Manage Lists         - Create and delete lists, add or remove columns in a list,
                         and add or remove public views of a list.
[ ] Override List Behaviors - Discard or check in a document checked out to another user,
                             change or override settings allowing read/edit only own items
[ ] Add Items            - Add items to lists and documents to document libraries.
[ ] Edit Items           - Edit items in lists, edit documents in doc libraries,
                         and customize Web Part Pages.
[ ] Delete Items         - Delete items from a list and documents from a document library.
[x] View Items           - View items in lists and documents in document libraries.
[ ] Approve Items        - Approve a minor version of a list item or document.
[x] Open Items           - View source of documents with server-side file handlers.
[ ] View Versions        - View past versions of a list item or document.

[Site Permissions]
[ ] Manage Permissions   - Create and change permission levels on the Web site,
                         assign permissions to users and groups.
[ ] View Web Analytics Data - View reports on Web site usage.
[ ] Create Subsites      - Create subsites (team sites, Meeting Workspace, Document Workspace).
[ ] Manage Web Site      - Perform administration tasks and manage content.
[ ] Add and Customize Pages - Add/change/delete HTML or Web Part Pages,
                             edit site using SharePoint Foundation-compatible editor.
[ ] Apply Themes and Borders - Apply a theme or borders to entire Web site.
[ ] Apply Style Sheets   - Apply a style sheet (.CSS file) to the Web site.
[ ] Create Groups        - Create user groups usable anywhere in site collection.
[ ] Browse Directories   - Enumerate files/folders using SharePoint Designer and Web DAV.
[ ] Use Self-Service Site Creation - Create Web site using Self-Service Site Creation.
[x] View Pages           - View pages in a Web site.
[ ] Enumerate Permissions - Enumerate permissions on Web site, list, folder, document, or list item.
[ ] Browse User Information - View information about users of the Web site.
[ ] Manage Alerts        - Manage alerts for all users of the Web site.
[ ] Use Remote Interfaces - Use SOAP, Web DAV, Client Object Model or SharePoint Designer
                           interfaces to access the Web site.
[ ] Use Client Integration Features - Use client applications features; without it,
                                     users must work on documents locally and upload changes.
[x] Open                 - Allows users to open a Web site, list or folder to access items inside.
[ ] Edit Personal User Information - Allows user to change own user info (e.g., add picture).

[Personal Permissions]
[ ] Manage Personal Views - Create, change, delete personal views of lists.
[ ] Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.
[ ] Update Personal Web Parts - Update Web Parts to display personalized information.

Legend: [x]=Checked [ ]=Unchecked
```

<transcription_notes>  
- Checked permissions: View Items, Open Items, View Pages, Open  
- Unchecked permission highlighted in red: Use Remote Interfaces  
- Green boxes highlight: View Items, Open Items, View Pages  
- Grey box highlight: Open  
- All other permissions unchecked  
</transcription_notes>  
</transcription_image>

---

<!-- PAGE 14 -->

```markdown
# View Only - Can read site, pages, lists, document libraries, files, items but not download and open files in Office Desktop Version

Name:  
View Only

Description:  
Can view pages, list items, and documents.  
Document types with server-side file handlers can be viewed in the browser but

Select the permissions to include in this permission level.

- [ ] Select All

### List Permissions

- [ ] Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.
- [ ] Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items
- [ ] Add Items - Add items to lists and add documents to document libraries.
- [ ] Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.
- [ ] Delete Items - Delete items from a list and documents from a document library.
- [x] View Items - View items in lists and documents in document libraries.
- [ ] Approve Items - Approve a minor version of a list item or document.
- [ ] Open Items - View the source of documents with server-side file handlers.  
  <span style="color:red;">(unchecked, red box highlight)</span>
- [x] View Versions - View past versions of a list item or document.

<!-- Column 2 -->

### Site Permissions

- [ ] Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.
- [ ] View Web Analytics Data - View reports on Web site usage.
- [ ] Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.
- [ ] Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.
- [ ] Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.
- [ ] Apply Themes and Borders - Apply a theme or borders to the entire Web site.
- [ ] Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.
- [ ] Create Groups - Create a group of users that can be used anywhere within the site collection.
- [ ] Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.
- [x] Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

- [x] Create Alerts - Create alerts.
- [x] View Application Pages - View forms, views, and application pages. Enumerate lists.
- [x] Browse User Information - View information about users of the Web site.
- [x] Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.
- [x] Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.
- [x] Open - Allows users to open a Web site, list, or folder in order to access items inside that container.

- [ ] Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.
- [ ] Manage Alerts - Manage alerts for all users of the Web site.
- [ ] Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

### Personal Permissions

- [ ] Manage Personal Views - Create, change, and delete personal views of lists.
- [ ] Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.
- [ ] Update Personal Web Parts - Update Web Parts to display personalized information.

> **Sidebar: Note**  
> Enable "SharePoint Server Enterprise Site Collection features" to get this. This combination can't be created manually.

---

<transcription_image>
**Figure 1: Permissions and Features for "View Only" Permission Level**

```ascii
[PERMISSION LEVEL: View Only]
Name: [View Only]
Description: Can view pages, list items, and documents.
Document types with server-side file handlers can be viewed in the browser but

[LIST PERMISSIONS]
[ ] Select All

[ ] Manage Lists
[ ] Override List Behaviors
[ ] Add Items
[ ] Edit Items
[ ] Delete Items
[x] View Items
[ ] Approve Items
[ ] Open Items [RED BOX] - View the source of documents with server-side file handlers.
[x] View Versions

[SITE PERMISSIONS]
[ ] Manage Permissions
[ ] View Web Analytics Data
[ ] Create Subsites
[ ] Manage Web Site
[ ] Add and Customize Pages
[ ] Apply Themes and Borders
[ ] Apply Style Sheets
[ ] Create Groups
[ ] Browse Directories
[x] Use Self-Service Site Creation

[x] Create Alerts
[x] View Application Pages
[x] Browse User Information
[x] Use Remote Interfaces
[x] Use Client Integration Features
[x] Open

[ ] Enumerate Permissions
[ ] Manage Alerts
[ ] Edit Personal User Information

[PERSONAL PERMISSIONS]
[ ] Manage Personal Views
[ ] Add/Remove Personal Web Parts
[ ] Update Personal Web Parts

Note: Enable "SharePoint Server Enterprise Site Collection features" to get this. This combination can't be created manually.

Legend: [x]=Checked [ ]=Unchecked
[RED BOX] = Open Items unchecked, red highlight
[GREEN BOX] = Multiple key permissions checked
```

<transcription_notes>
- All checked permissions are enclosed in green boxes in original image.
- "Open Items" permission is unchecked and highlighted with red box.
- Blue arrows and annotations emphasize that "Use Self-Service Site Creation" and "View Versions" must be enabled together.
- Text colors: "View Only" in blue, "but not download and open files in Office Desktop Version" in red.
- Some checkboxes are greyed out or surrounded by grey boxes representing grouping UI.
- No numeric data present.
</transcription_notes>
</transcription_image>
```

---

<!-- PAGE 15 -->

# Read - Can read site, pages, lists, document libraries, files, items and download / open in Desktop Version

Name:  
Read

Description:  
Can view pages and list items and download documents.

Select the permissions to include in this permission level.

- [ ] Select All

## List Permissions

- [ ] Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.
- [ ] Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items
- [ ] Add Items - Add items to lists and add documents to document libraries.
- [ ] Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.
- [ ] Delete Items - Delete items from a list and documents from a document library.
- [x] View Items - View items in lists and documents in document libraries.
- [ ] Approve Items - Approve a minor version of a list item or document.
- [x] Open Items - View the source of documents with server-side file handlers.
- [x] View Versions - View past versions of a list item or document.

- [ ] Delete Versions - Delete past versions of a list item or document.

- [x] Create Alerts - Create alerts.
- [x] View Application Pages - View forms, views, and application pages. Enumerate lists.

## Site Permissions

- [ ] Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.
- [ ] View Web Analytics Data - View reports on Web site usage.
- [ ] Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.
- [ ] Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.
- [ ] Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.
- [ ] Apply Themes and Borders - Apply a theme or borders to the entire Web site.
- [ ] Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.
- [ ] Create Groups - Create a group of users that can be used anywhere within the site collection.
- [ ] Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.
- [x] Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

- [x] View Pages - View pages in a Web site.
- [ ] Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.
- [x] Browse User Information - View information about users of the Web site.

- [ ] Manage Alerts - Manage alerts for all users of the Web site.
- [x] Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.
- [x] Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.
- [x] Open - Allows users to open a Web site, list, or folder in order to access items inside that container.
- [ ] Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

## Personal Permissions

- [ ] Manage Personal Views - Create, change, and delete personal views of lists.
- [ ] Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.
- [ ] Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> Page 1 | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 16 -->

# Contribute - Can fully use site but not change lists, document libraries, settings or pages

Name:  
Contribute

Description:  
Can view, add, update, and delete list items and documents.

Select the permissions to include in this permission level.

- [ ] Select All

### List Permissions

- [ ] Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.

- [ ] Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items

- [x] Add Items - Add items to lists and add documents to document libraries  
- [x] Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.  
- [x] Delete Items - Delete items from a list and documents from a document library.  
- [x] View Items - View items in lists and documents in document libraries.

- [ ] Approve Items - Approve a minor version of a list item or document.

- [x] Open Items - View the source of documents with server-side file handlers.  
- [x] View Versions - View past versions of a list item or document.

---

### Site Permissions

- [ ] Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.

- [ ] View Web Analytics Data - View reports on Web site usage.

- [ ] Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.

- [ ] Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.

- [ ] Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.

- [ ] Apply Themes and Borders - Apply a theme or borders to the entire Web site.

- [ ] Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.

- [ ] Create Groups - Create a group of users that can be used anywhere within the site collection.

- [x] Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.

- [x] Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

- [x] Delete Versions - Delete past versions of a list item or document.

- [x] Create Alerts - Create alerts.

- [x] View Application Pages - View forms, views, and application pages. Enumerate lists.

- [x] View Pages - View pages in a Web site.

- [ ] Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.

- [x] Browse User Information - View information about users of the Web site.

- [ ] Manage Alerts - Manage alerts for all users of the Web site.

- [x] Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.

- [x] Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.

- [x] Open - Allows users to open a Web site, list, or folder in order to access items inside that container.

- [x] Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

#### Personal Permissions

- [x] Manage Personal Views - Create, change, and delete personal views of lists.

- [x] Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.

- [x] Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 17 -->

```markdown
# Edit - Can fully use site and change list / document library settings but not change settings or pages

**Name:**  
Edit

**Description:**  
Can add, edit and delete lists; can view, add, update and delete list items and documents.

Select the permissions to include in this permission level.  
☐ Select All

## List Permissions

☑ Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.

☐ Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items

☑ Add Items - Add items to lists and add documents to document libraries  
☑ Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.  
☑ Delete Items - Delete items from a list and documents from a document library.  
☑ View Items - View items in lists and documents in document libraries.

☐ Approve Items - Approve a minor version of a list item or document.

☑ Open Items - View the source of documents with server-side file handlers.  
☑ View Versions - View past versions of a list item or document.

☑ Delete Versions - Delete past versions of a list item or document.  
☑ Create Alerts - Create alerts.  
☑ View Application Pages - View forms, views, and application pages. Enumerate lists.

## Site Permissions

☐ Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.

☐ View Web Analytics Data - View reports on Web site usage.

☐ Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.

☐ Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.

☐ Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.

☐ Apply Themes and Borders - Apply a theme or borders to the entire Web site.

☐ Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.

☐ Create Groups - Create a group of users that can be used anywhere within the site collection.

☑ Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.  
☑ Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

☐ View Pages - View pages in a Web site.

☐ Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.

☑ Browse User Information - View information about users of the Web site.

☐ Manage Alerts - Manage alerts for all users of the Web site.

☑ Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.  
☑ Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.  
☑ Open - Allows users to open a Web site, list, or folder in order to access items inside that container.  
☑ Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

## Personal Permissions

☑ Manage Personal Views - Create, change, and delete personal views of lists.  
☑ Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.  
☑ Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> 17 </transcription_page_footer>
```


---

<!-- PAGE 18 -->

# Approve - Can fully use site and approve items but not change settings or pages

Name:  
Approve

Description:  
Can edit and approve pages, list items, and documents.

Select the permissions to include in this permission level.

☐ Select All

### List Permissions

☐ Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.  
☑ Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items  
☑ Add Items - Add items to lists and add documents to document libraries  
☑ Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.  
☑ Delete Items - Delete items from a list and documents from a document library.  
☑ View Items - View items in lists and documents in document libraries.  
☑ Approve Items - Approve a minor version of a list item or document.  
☑ Open Items - View the source of documents with server-side file handlers.  
☑ View Versions - View past versions of a list item or document.

### Site Permissions

☐ Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.  
☐ View Web Analytics Data - View reports on Web site usage.  
☐ Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.  
☐ Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.  
☐ Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.  
☐ Apply Themes and Borders - Apply a theme or borders to the entire Web site.  
☐ Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.  
☐ Create Groups - Create a group of users that can be used anywhere within the site collection.  
☑ Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.  
☑ Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

☑ Delete Versions - Delete past versions of a list item or document.  
☑ Create Alerts - Create alerts.  
☑ View Application Pages - View forms, views, and application pages. Enumerate lists.  
☐ View Pages - View pages in a Web site.  
☐ Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.  
☑ Browse User Information - View information about users of the Web site.  
☐ Manage Alerts - Manage alerts for all users of the Web site.

☑ Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.  
☑ Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.  
☑ Open - Allows users to open a Web site, list, or folder in order to access items inside that container.  
☑ Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

### Personal Permissions

☑ Manage Personal Views - Create, change, and delete personal views of lists.  
☑ Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.  
☑ Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> Page 1 | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 19 -->

```markdown
# Design - Can fully use site, approve items, modify Look & Feel but not modify permissions and groups

Name:  
Design

Description:  
Can view, add, update, delete, approve, and customize.

Select the permissions to include in this permission level.  
☐ Select All

## List Permissions

- ☑ Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.

- ☑ Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items

- ☑ Add Items - Add items to lists and add documents to document libraries

- ☑ Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.

- ☑ Delete Items - Delete items from a list and documents from a document library.

- ☑ View Items - View items in lists and documents in document libraries.

- ☑ Approve Items - Approve a minor version of a list item or document.

- ☑ Open Items - View the source of documents with server-side file handlers.

- ☑ View Versions - View past versions of a list item or document.

- ☑ Delete Versions - Delete past versions of a list item or document.

- ☑ Create Alerts - Create alerts.

- ☑ View Application Pages - View forms, views, and application pages. Enumerate lists.

## Site Permissions

- ☐ Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.

- ☐ View Web Analytics Data - View reports on Web site usage.

- ☐ Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.

- ☐ Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.

- ☑ Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.

- ☑ Apply Themes and Borders - Apply a theme or borders to the entire Web site.

- ☑ Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.

- ☐ Create Groups - Create a group of users that can be used anywhere within the site collection.

- ☑ Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.

- ☑ Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

- ☐ View Pages - View pages in a Web site.

- ☐ Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.

- ☑ Browse User Information - View information about users of the Web site.

- ☐ Manage Alerts - Manage alerts for all users of the Web site.

- ☑ Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.

- ☑ Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.

- ☑ Open - Allows users to open a Web site, list, or folder in order to access items inside that container.

- ☑ Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

## Personal Permissions

- ☑ Manage Personal Views - Create, change, and delete personal views of lists.

- ☑ Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.

- ☑ Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> 19 </transcription_page_footer>
```


---

<!-- PAGE 20 -->

```markdown
# Manage Hierarchy - Can fully use site, modify groups and permissions but not modify Look & Feel and approve items

Name:  
Manage Hierarchy

Description:  
Can create sites and edit pages, list items, and documents.

Select the permissions to include in this permission level.  
☐ Select All

## List Permissions

- ☑ Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.
- ☐ Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items
- ☑ Add Items - Add items to lists and add documents to document libraries
- ☑ Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.
- ☑ Delete Items - Delete items from a list and documents from a document library.
- ☑ View Items - View items in lists and documents in document libraries.
- ☐ Approve Items - Approve a minor version of a list item or document.

- ☑ Open Items - View the source of documents with server-side file handlers.
- ☑ View Versions - View past versions of a list item or document.

## Site Permissions

- ☑ Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.
- ☑ View Web Analytics Data - View reports on Web site usage.
- ☑ Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.
- ☑ Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.

- ☐ Apply Themes and Borders - Apply a theme or borders to the entire Web site.
- ☐ Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.

- ☐ Create Groups - Create a group of users that can be used anywhere within the site collection.

- ☑ Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.
- ☑ Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

- ☑ View Pages - View pages in a Web site.
- ☑ Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.
- ☐ Browse User Information - View information about users of the Web site.

- ☑ Manage Alerts - Manage alerts for all users of the Web site.

- ☐ Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.
- ☐ Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.
- ☐ Open - Allows users to open a Web site, list, or folder in order to access items inside that container.
- ☐ Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

## Personal Permissions

- ☑ Manage Personal Views - Create, change, and delete personal views of lists.
- ☑ Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.
- ☑ Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> Page 20 | VATTENFALL </transcription_page_footer>
```

---

```markdown
<transcription_image>
**Figure 1: Manage Hierarchy Permissions Interface with Permission Categories and Checkboxes**

```ascii
+-----------------------------------------------------+  +-----------------------------------+  +-----------------------------------+
| Name: Manage Hierarchy                              |  | [X] Delete Versions               |  | [X] View Pages                    |
| Description:                                        |  |     - Delete past versions...     |  |     - View pages in a Web site.   |
| Can create sites and edit pages, list items, and   |  | [X] Create Alerts                 |  | [X] Enumerate Permissions         |
| documents.                                          |  |     - Create alerts.              |  |     - Enumerate permissions on   |
|                                                     |  | [X] View Application Pages       |  |       Web site, list, folder,     |
| Select the permissions:                             |  |     - View forms, views...        |  |       document, or list item.     |
| [ ] Select All                                     |  +-----------------------------------+  +-----------------------------------+
|                                                     |
| List Permissions                                    |
| [X] Manage Lists - Create and delete lists, add or |  +--------------------------------------------------+
|     remove columns in a list, and add or remove    |  | Site Permissions                                |
|     public views of a list.                        |  | [X] Manage Permissions - Create and change       |
| [ ] Override List Behaviors - Discard or check in |  |     permission levels on the Web site and assign |
|     a document checked out to another user...     |  |     permissions to users and groups.             |
| [X] Add Items - Add items to lists and add         |  | [X] View Web Analytics Data - View reports on     |
|     documents to libraries                         |  |     Web site usage.                              |
| [X] Edit Items - Edit items in lists, edit docs   |  | [X] Create Subsites - Create subsites such as     |
|     in libs, customize Web Part Pages             |  |     team sites, Meeting Workspace sites, and      |
| [X] Delete Items - Delete items from lists and docs|  |     Document Workspace sites.                     |
| [X] View Items - View items in lists and docs     |  | [X] Manage Web Site - Grants ability to perform   |
| [ ] Approve Items - Approve minor versions         |  |     all admin tasks and manage content.           |
|                                                     |  +--------------------------------------------------+
| [X] Open Items - View source of docs with server- |  +--------------------------------------------------+
|     side file handlers                             |  | [ ] Apply Themes and Borders - Apply theme or     |
| [X] View Versions - View past versions             |  |     borders to entire Web site                    |
|                                                     |  | [ ] Apply Style Sheets - Apply .CSS file to site  |
|                                                     |  | [ ] Create Groups - Create a group usable sitewide|
|                                                     |  | [X] Browse Directories - Enumerate files and       |
|                                                     |  |     folders using SharePoint Designer and Web DAV |
|                                                     |  | [X] Use Self-Service Site Creation - Create a Web  |
|                                                     |  |     site using Self-Service Site Creation          |
|                                                     |  +--------------------------------------------------+
|                                                     |  +--------------------------------------------------+
|                                                     |  | [ ] Use Remote Interfaces - SOAP, Web DAV, Client |
|                                                     |  |     Object Model, SharePoint Designer interfaces  |
|                                                     |  | [ ] Use Client Integration Features - Launch client|
|                                                     |  |     applications; without permission local edits  |
|                                                     |  | [ ] Open - Open Web site, list, or folder          |
|                                                     |  | [ ] Edit Personal User Information - Change own    |
|                                                     |  |     user info, e.g. add picture                     |
|                                                     |  +--------------------------------------------------+
|                                                     |  +--------------------------------------------------+
|                                                     |  | Personal Permissions                             |
|                                                     |  | [X] Manage Personal Views - Create, change, delete|
|                                                     |  |     personal views of lists                        |
|                                                     |  | [X] Add/Remove Personal Web Parts - Add/remove    |
|                                                     |  |     personal Web Parts on Web Part Page           |
|                                                     |  | [X] Update Personal Web Parts - Update Web Parts  |
|                                                     |  |     for personalized info                          |
|                                                     |  +--------------------------------------------------+
+-----------------------------------------------------+

Legend: [X]=Checked permission  [ ]=Unchecked permission

```
<transcription_notes>
- All text and permission option details fully transcribed.
- Checkboxes correspond to allowed (checked) or disallowed (unchecked) permissions.
- Red highlight indicates "Approve Items" and "Apply Themes and Borders"/"Apply Style Sheets" unchecked.
- Green highlight indicates allowed permissions in List and Site Permissions.
- No color in ASCII.
</transcription_notes>
</transcription_image>
```


---

<!-- PAGE 21 -->

# Full Control - All available permissions for lists, items, site, groups, permissions, settings and access

Name:  
Full Control

Description:  
Has full control.

Select the permissions to include in this permission level.  
☐ Select All

---

### List Permissions

- ☑ Manage Lists - Create and delete lists, add or remove columns in a list, and add or remove public views of a list.  
- ☑ Override List Behaviors - Discard or check in a document which is checked out to another user, and change or override settings which allow users to read/edit only their own items  
- ☑ Add Items - Add items to lists and add documents to document libraries  
- ☑ Edit Items - Edit items in lists, edit documents in document libraries, and customize Web Part Pages in document libraries.  
- ☑ Delete Items - Delete items from a list and documents from a document library.  
- ☑ View Items - View items in lists and documents in document libraries.  
- ☑ Approve Items - Approve a minor version of a list item or document.

---

- ☑ Open Items - View the source of documents with server-side file handlers.  
- ☑ View Versions - View past versions of a list item or document.

---

### Site Permissions

- ☑ Delete Versions - Delete past versions of a list item or document.  
- ☑ Create Alerts - Create alerts.  
- ☑ View Application Pages - View forms, views, and application pages. Enumerate lists.

- **Site Permissions**  
  - ☑ Manage Permissions - Create and change permission levels on the Web site and assign permissions to users and groups.  
  - ☑ View Web Analytics Data - View reports on Web site usage.  
  - ☑ Create Subsites - Create subsites such as team sites, Meeting Workspace sites, and Document Workspace sites.  
  - ☑ Manage Web Site - Grants the ability to perform all administration tasks for the Web site as well as manage content.  
  - ☑ Add and Customize Pages - Add, change, or delete HTML pages or Web Part Pages, and edit the Web site using a Microsoft SharePoint Foundation-compatible editor.

---

- ☑ Apply Themes and Borders - Apply a theme or borders to the entire Web site.  
- ☑ Apply Style Sheets - Apply a style sheet (.CSS file) to the Web site.  
- ☑ Create Groups - Create a group of users that can be used anywhere within the site collection.

---

- ☑ Browse Directories - Enumerate files and folders in a Web site using SharePoint Designer and Web DAV interfaces.  
- ☑ Use Self-Service Site Creation - Create a Web site using Self-Service Site Creation.

---

- ☑ View Pages - View pages in a Web site.  
- ☑ Enumerate Permissions - Enumerate permissions on the Web site, list, folder, document, or list item.  
- ☑ Browse User Information - View information about users of the Web site.  
- ☑ Manage Alerts - Manage alerts for all users of the Web site.  
- ☑ Use Remote Interfaces - Use SOAP, Web DAV, the Client Object Model or SharePoint Designer interfaces to access the Web site.  
- ☑ Use Client Integration Features - Use features which launch client applications. Without this permission, users will have to work on documents locally and upload their changes.  
- ☑ Open - Allows users to open a Web site, list, or folder in order to access items inside that container.  
- ☑ Edit Personal User Information - Allows a user to change his or her own user information, such as adding a picture.

---

### Personal Permissions

- ☑ Manage Personal Views - Create, change, and delete personal views of lists.  
- ☑ Add/Remove Personal Web Parts - Add or remove personal Web Parts on a Web Part Page.  
- ☑ Update Personal Web Parts - Update Web Parts to display personalized information.

<transcription_page_footer> 21 </transcription_page_footer>

---

<!-- PAGE 22 -->

```markdown
# Mastering SharePoint Permissions

## How to add people to SharePoint groups

<transcription_image>
**Figure 1: Cartoon raccoon with question mark**

```ascii
[Cartoon raccoon character with a question mark on its chest]
Legend: [unclear: cartoon character] = raccoon
```

<transcription_notes>
- No numeric data present
- Colors: Grey and pink for raccoon, blue question mark, green platform, light blue circle border
- ASCII misses: Character details and colors
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>
```


---

<!-- PAGE 23 -->

# How to add people to SharePoint groups

<!-- Column 1 -->
## Classic

- A) Use the "Share" button on the classic Homepage  
- B) Site Contents > Site Settings > People and groups > click on group > New > Add Users  
- C) Site Settings > Site permissions > click on group > New > Add Users  

<transcription_image>
**Figure 1: Classic SharePoint adding users flow with UI screenshots and labeled steps**

```ascii
[PROCESS] "Site Contents"  
    ↓  
[PROCESS] "Site Settings"  
    ↓  
[PROCESS] "Site permissions"  
    ↓  
[PROCESS] "click on group"  
    ↓  
[PROCESS] "New > Add Users"

[PROCESS] "People and groups"  
    ↓  
[PROCESS] "click on group"  
    ↓  
[PROCESS] "New > Add Users"

[PROCESS] "Share" button on classic Homepage
```

<transcription_notes>
- UI screenshots show navigation from Site Contents → Site Settings → Site permissions → group selection → New > Add Users
- Red boxes highlight clickable options: "Site Contents," "Site Settings," "Site permissions"
- Arrows indicate flow path
</transcription_notes>
</transcription_image>

<!-- Column 2 -->
## Modern

- Cogwheel icon (top right) > Site permissions > Advanced permission settings > click on group > New > Add Users

<transcription_image>
**Figure 2: Modern SharePoint adding users flow with UI screenshots and labeled steps**

```ascii
[PROCESS] Cogwheel icon (top right)  
    ↓  
[PROCESS] "Site permissions"  
    ↓  
[PROCESS] "Advanced permission settings"  
    ↓  
[PROCESS] click on group  
    ↓  
[PROCESS] New > Add Users
```

<transcription_notes>
- UI screenshots show clicking the cogwheel icon > Settings menu with "Site permissions" highlighted > Permissions panel with "Advanced permissions settings" link highlighted
- Red boxes highlight clickable UI elements: Cogwheel icon, "Site permissions," "Advanced permissions settings"
- Arrows indicate user navigation flow
</transcription_notes>
</transcription_image>

<transcription_page_footer> Page 1 | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 24 -->

# Where to find the site administrators

## Classic

- No way. Owners can't see who is admin.

<transcription_image>
**Figure 1: Classic site collection administrators dialog**

```ascii
[PROCESS] Site Collection Administrators Window
+--------------------------------------------------------------+
| Site Collection Administrators                                |
|                                                              |
| Site Collection Administrators                               |
| Site Collection Administrators                               |
| are given full control over all                               |
| Web sites in the site                                        |
| collection. They may also                                    |
| receive site use confirmation                               |
| mail. Enter users separated by                              |
| semicolons.                                                 |
|                                                              |
| +--------------------------------------------------------+   |
| | Company Administrator x                                  |   |
| | SharePoint Online Admin (YIOHW) x                        |   |
| | SharePoint Service Administrator x                       |   |
| +--------------------------------------------------------+   |
|                                                              |
|                     [OK]     [Cancel]                        |
+--------------------------------------------------------------+
```
<transcription_notes>
- Data: User list includes "Company Administrator", "SharePoint Online Admin (YIOHW)", "SharePoint Service Administrator"
- Red box highlights "Site Collection Administrators" tab and section
- Context: Owners cannot see who is admin in Classic interface
</transcription_notes>
</transcription_image>

## Modern

- Cogwheel icon (top right) > Site permissions > Advanced permission settings > Site Collection Administrators

<transcription_image>
**Figure 2: Modern site permissions navigation**

```ascii
[PROCESS] Modern SharePoint Permissions Navigation Flow

[Cogwheel Icon] --arrow--> [Settings Menu]
                             |
                             +--> Site permissions [red box]
                                   |
                                   +--> Permissions Dialog
                                         |
                                         +--> Advanced permissions settings [red box]

Legend: [Cogwheel Icon]=Settings button
```
<transcription_notes>
- Data: Navigation path detailed as cogwheel icon to Site permissions to Advanced permission settings to Site Collection Administrators
- Red boxes highlight "Site permissions" in settings and "Advanced permissions settings" in permissions dialog
- Images show UI screenshots with red rectangles marking these clickable items
</transcription_notes>
</transcription_image>

<transcription_page_footer> Page 1 | Vattenfall </transcription_page_footer>

---

<!-- PAGE 25 -->

# What on only admins can do

- Assign other administators  
- Entirely delete users from Site Collection  
- Toggle Site Collection Features  
- See the secondary Recycle Bin and restore / delete items from it  
- Delete the Site Collection  
- Modify advanced search settings  
- Modify language variation settings  
- Use Powershell  

<transcription_page_footer> Page [unclear] | Vattenfall </transcription_page_footer>

---

<!-- PAGE 26 -->

```markdown
# Mastering SharePoint Permissions

## How does individual sharing change permissions

Confidentiality: C2 - Internal

VATTENFALL
```


---

<!-- PAGE 27 -->

# How SharePoint permissions work

<transcription_image>
**Figure 1: How SharePoint permissions work**

```ascii
HOW SHAREPOINT PERMISSIONS WORK

[Site Objects]       [Permission Levels]       [Groups]           [Users]

+------------+       +---------------+         +----------+       (●) (●)
|  Site      |<------| Full Control  |<--------|  Owner   |<------(●) (●) (●) (●)
+------------+       +---------------+         +----------+       

   ^ inherits from         +----------+              +----------+       
   |                      | Edit     |<-------------| Member   |<------(●) (●) (●) (●)
   |                      +----------+              +----------+       

   | inherits from         +----------+              +----------+       
   |                      | Read     |<-------------| Visitors |<------(●)
   |                      +----------+              +----------+       

   ^ inherits from
+--------------+
| List/Library |
+--------------+

   ^ inherits from
+---------+
| Folder  |
+---------+

   ^ inherits from
+------------+
| Item/File  |
+------------+

Arrows above boxes show inheritance of permissions from lower to higher objects.
Arrows from right to left indicate assignment of permission levels to site objects.
Arrows from groups to permission levels show groups have permission levels.
Arrows from users to groups indicate users belong to groups.

Text above arrows:
- From Site Objects to Permission Levels: "define object permissions"
- From Permission Levels to Groups: "have permission level"
- From Groups to Users: "belong to groups"
```

<transcription_notes>
- Data: No numeric data to extract.
- Colors: Blue = labels, arrows, and boxes.
- ASCII misses: User icons replaced by (●) for persons.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 28 -->

# Permissions for a folder

<transcription_image>
**Figure 1: Permissions inheritance flow for site objects and SharePoint permissions UI**

```ascii
PERMISSIONS FOR A FOLDER

Site Objects:
             +--------+
             |  Site  |  <-- inherits from
             +--------+
                 |
                 v
        +------------------+
        |  List / Library  |  <-- inherits from
        +------------------+
                 |
                 v
           +----------+
           |  Folder  |  (in red)
           +----------+
                 |
                 v
         +-------------+
         | Item / File |
         +-------------+

[Right side: SharePoint Permissions UI snippet]

Permission Inheritance = On
[Arrow pointing to "Stop Inheriting Permissions" icon in toolbar]

Message box:
"There are limited access users on this site. Users may have limited access if an item or document under the site has been shared with
This document inherits permissions from its parent. (My SharePoint Site)"

List of SharePoint Groups and Permission Levels:

 Name                              | Type              | Permission Levels
----------------------------------|-------------------|---------------------------
 Approvers                        | SharePoint Group  | Approve
 Designers                        | SharePoint Group  | Design
 Excel Services Viewers           | SharePoint Group  | View Only
 Hierarchy Managers              | SharePoint Group  | Manage Hierarchy
 Restricted Readers              | SharePoint Group  | Restricted Read
 SharePoint SupportTest Members  | SharePoint Group  | Edit
 SharePoint SupportTest Owners   | SharePoint Group  | Full Control
 SharePoint SupportTest Visitors | SharePoint Group  | Read
 Translation Managers            | SharePoint Group  | Restricted Interfaces for Translation
```

<transcription_notes>
- Data: hierarchy flow Site → List/Library → Folder → Item/File
- Permission inheritance status: On
- SharePoint Groups and their permission levels listed as above
- Colors: Folder box in red to highlight, others in blue
- Arrow labeled "Permission Inheritance = On" points to "Stop Inheriting Permissions" button
- UI screenshot content included as text
</transcription_notes>
</transcription_image>

---

<!-- PAGE 29 -->

# Individually sharing a folder

## Site Objects, Permission Levels, Groups, Users

<!-- Column 1 -->
**Site Objects**

```ascii
[Site] <--- inherits from ---+
                             |
[List / Library] <--- inherits from ---+
                                        |
[Folder] <--- inherits from ---+
                                 |
[Item / File]
```

<!-- Column 2 -->
**Permission Levels**

(Screenshot showing a folder selected with sharing icon highlighted)

Dialog:  
Send Link  
- People you specify can edit  
- Enter a name or email address  
- Add a message (optional)  
- Buttons: Send, Copy Link

Dialog:  
Link settings  
- Who would you like this link to work for?  
  - Anyone with the link  
  - People in Vattenfall AB with the link  
  - People with existing access  
  - Specific people (selected)  
- Other settings:  
  - Allow editing (checked)  
- Buttons: Apply, Cancel

<!-- Column 3 -->
**Groups**

[No additional text visible]

<!-- Column 4 -->
**Users**

Icon of user → Other internal or external User

---

<transcription_image>
**Figure 1: Individually sharing a folder in site objects hierarchy**

```ascii
SITE OBJECTS HIERARCHY

[Site]
   |
   v inherits from
[List / Library]
   |
   v inherits from
[Folder] ------------- (red arrow) --------------> [Other internal or external User icon]
   |
   v inherits from
[Item / File]
```

Legend:  
[Site], [List / Library], [Folder], [Item / File] = Site Objects  
(red arrow) = Sharing link to user  

<transcription_notes>
- The hierarchy shows inheritance of permissions from Site down to Item/File.
- Folder is highlighted in red, indicating the level at which sharing is occurring.
- Permission dialogs show sharing a folder with specific people with editing rights enabled.
- Users represented by an icon labeled "Other internal or external User".
- Visual screenshots included but not transcribed in detail.
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 30 -->

# How individual sharing changes permissions

## Step 1 Permission Inheritance is broken

<!-- Column 1 -->
### Site Objects

- Site  
- List / Library  
- Folder  
- Item / File  

### Permission Levels

- Full Control  
- Edit  
- Read  
- Edit (highlighted in red)

### Groups

- Owner  
- Member  
- Visitors  

### Users

- Icons representing users:  
  - Owner group: 2 users  
  - Member group: 4 users  
  - Visitors group: 1 user  
  - Other internal or external User: 1 user  

<transcription_image>
**Figure 1: How individual sharing changes permissions - Step 1 Permission Inheritance is broken**

```ascii
[Site Objects]               [Permission Levels]            [Groups]               [Users]

 +---------+                  +--------------+              +---------+          (o) (o)
 |  Site   | <--------------  | Full Control | <----------  | Owner   |          
 +---------+                  +--------------+              +---------+          
     ^                             ^                           ^                (o) (o) (o) (o)
     | inherits from               |                           | <----------  | Member  |
 +-------------+                  +---------+                 +----------+          
 | List/Library|                  |  Edit   | <-------------  | Member   |          
 +-------------+                  +---------+                 +----------+          
     |                             |                           |                (o)
     |                             |                           | <----------  | Visitors|
 +------------+                   +-------+                   +----------+          
 | Item/File  |                   | Read  |                   | Visitors |           
 +------------+                   +-------+                   +----------+          
                                   |                                              (o)
                                   |                                              |
                                   | <--------------------------------------------+
                                   |                                              | Other internal 
                                   |                                              | or external User
                                   |                                              |
                               +---------+                                        
                               |  Edit   |                                        
                               +---------+                                        
                                   ^                                             
                                   | gets direct                                  
                                   | permission level                             
                                   +----------------------------------------------+

Legend:  
[o] = User icon  
Red box = Folder and Edit permission highlighted in red  
Blue boxes = other items and permissions  
Arrows show inheritance and permission assignment  
```

<transcription_notes>
- Data: No numeric data, only labels and user counts (2, 4, 1, 1 users)
- Colors: Blue = default permissions and items; Red = broken inheritance and direct edit permission
- Arrows show inheritance flow and permission assignment
- User icons shown as circles (o)
- "Permission Inheritance is broken" is emphasized in red
</transcription_notes>
</transcription_image>

---

<!-- PAGE 31 -->

# How individual sharing changes permissions

## Step 2 User is added to site with "Limited Access"

<transcription_image>
**Figure 1: How individual sharing changes permissions in Step 2**

```ascii
HOW INDIVIDUAL SHARING CHANGES PERMISSIONS

Site Objects         Permission Levels       Groups              Users

  +--------+            +--------------+      +--------------------+      (New User)
  | Site   |<-----------| Limited      |<-----| Limited Access      |       O
  |        |   inherits | Access       |      | System Group       |     [user icon]
  +--------+    from   +--------------+      +--------------------+       |
     ^                        |  no access to site                       |
     |                                                              -----
     |                                                               |
  inherits from                                                      |
     |                                                              |
  +--------------+        +---------+                              -----
  | List /       |<-------| Edit    |<-----------------------------> (New User)
  | Library      |        +---------+                                [user icon]
  +--------------+                                               
   inheritance is broken                                  

  +------------+    
  | Item / File|    
  +------------+    
```
Legend:  
- Boxes represent entities: `[Site Objects]`, `[Permission Levels]`, `[Groups]`, `[Users]`  
- Arrows show inheritance or permission flow  
- Blue boxes and text are standard objects  
- Red boxes and arrows indicate limited access and edit permissions  
- "Limited Access System Group" is a group that grants Limited Access permission to Site and List/Library  
- "New User" is assigned to the Limited Access System Group and given Edit permission on Folder

<transcription_notes>
- Data: No numerical data present  
- Colors: Blue = standard objects/text, Red = limited access/edit permissions and related arrows  
- ASCII misses: user icon shown as "O" with label [user icon], arrow styles simplified  
</transcription_notes>
</transcription_image>

---

<!-- PAGE 32 -->

# Permissions of a shared folder

<!-- Column 1 -->
## Site Objects

```ascii
[Site Objects]

   ┌────────┐
   │  Site  │  <-- inherits from
   └────────┘
        ↑
        │
┌────────────────┐
│ List / Library │
└────────────────┘

inheritance is broken

   ┌────────┐
   │ Folder │  <-- inherits from
   └────────┘
        ↑
        │
┌─────────────┐
│ Item / File │
└─────────────┘
```

<!-- Column 2 -->
## Permissions Interface Screenshot

```
[PERMISSIONS TAB - SHAREPOINT]

[Toolbar with buttons:]
- Delete unique permissions
- Grant Permissions
- Edit User Permissions
- Remove User Permissions
- Check Permissions

[Highlighted text:]
This document has unique permissions.

[List of users/groups with permissions:]

Name                          | Type               | Permission Levels
------------------------------|--------------------|----------------------------
Approvers                     | SharePoint Group   | Approve
Designers                     | SharePoint Group   | Design
Excel Services Viewers        | SharePoint Group   | View Only
Hierarchy Managers            | SharePoint Group   | Manage Hierarchy
Karsten Held                 | User               | Edit  <--- Highlighted in red box
Restricted Readers            | SharePoint Group   | Restricted Read
SharePoint SupportTest Members| SharePoint Group   | Edit
SharePoint SupportTest Owners | SharePoint Group   | Full Control
SharePoint SupportTest Visitors| SharePoint Group  | Read
Translation Managers          | SharePoint Group   | Restricted Interfaces for Translation

[Red arrow pointing from "Delete unique permissions" button to highlighted text:]
Permission Inheritance = Off
```

<transcription_image>
**Figure 1: Permissions of a shared folder**

```ascii
[SITE OBJECTS INHERITANCE]

Site Objects:
  ┌────────┐
  │  Site  │ <--- inherits from ---┐
  └────────┘                      │
                                 │ inheritance broken
  ┌────────────────┐             ↓
  │ List / Library │            ┌────────┐
  └────────────────┘            │ Folder │ <--- inherits from ---┐
                               └────────┘                      │
                                                              ↓
                                                    ┌─────────────┐
                                                    │ Item / File │
                                                    └─────────────┘


[PERMISSIONS UI]

[Toolbar:]
[Delete unique permissions] [Grant Permissions] [Edit User Permissions] [Remove User Permissions] [Check Permissions]

[Highlighted notice:]
This document has unique permissions.

[User list:]
Name                          | Type               | Permission Levels
------------------------------|--------------------|----------------------------
Approvers                     | SharePoint Group   | Approve
Designers                     | SharePoint Group   | Design
Excel Services Viewers        | SharePoint Group   | View Only
Hierarchy Managers            | SharePoint Group   | Manage Hierarchy
Karsten Held                 | User               | Edit  <-- Highlighted in red box
Restricted Readers            | SharePoint Group   | Restricted Read
SharePoint SupportTest Members| SharePoint Group   | Edit
SharePoint SupportTest Owners | SharePoint Group   | Full Control
SharePoint SupportTest Visitors| SharePoint Group  | Read
Translation Managers          | SharePoint Group   | Restricted Interfaces for Translation

[Red arrow from 'Delete unique permissions' button to highlighted text:]
Permission Inheritance = Off
```

<transcription_notes>
- Data: List of users/groups with types and permission levels as shown.
- Colors: Blue boxes = standard inheritance; red box = broken inheritance (Folder).
- Red arrow indicates "Permission Inheritance = Off".
- UI text exactly transcribed.
- "inheritance is broken" text in red below List/Library box.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 33 -->

# Granting permissions to a shared folder

<!-- Column 1 -->
## Site Objects

```ascii
SITE PERMISSION INHERITANCE

   [Site]  <--- inherits from --- [List / Library]
      ↑
      |  inheritance is broken (red text)
      |
   [Folder]  <--- inherits from --- [Item / File]

Legend:
[Site], [List / Library], [Folder], [Item / File] = Site Objects
```

<!-- Column 2 -->
Screenshot of a permissions UI showing:

- Permissions tab selected with icons:
  - Delete unique permissions
  - Grant Permissions (highlighted with red box)
  - Edit User Permissions
  - Remove User Permissions
  - Check Permissions

- A yellow banner: "This document has unique permissions."

- A "Share 'Master'" dialog with tabs:
  - Invite people (selected)
  - Get a link
  - Shared with

- Inside Invite people:
  - Text box: "Enter names or email addresses..."
  - Text area: "Include a personal message with this invitation (Optional)."
  - Checkbox: "Send an email invitation"
  - Dropdown: "Select a permission level" with "Edit" selected
  - Buttons: "Share" (blue), "Cancel"

<transcription_image>
**Figure 1: Site object permission inheritance and granting permissions UI**

```ascii
SITE PERMISSION INHERITANCE

   [Site]  <--- inherits from --- [List / Library]
      ↑
      |  inheritance is broken (red text)
      |
   [Folder]  <--- inherits from --- [Item / File]

Legend:
[Site], [List / Library], [Folder], [Item / File] = Site Objects
```

<transcription_notes>
- Colors: Blue boxes = inherited objects; Red box = Folder (inheritance broken)
- UI: "Grant Permissions" icon is highlighted with red box
- Text in red: "inheritance is broken"
- Screenshot data: Unique permissions warning, sharing dialog with invitation options
</transcription_notes>
</transcription_image>

---

<!-- PAGE 34 -->

# Editing permissions of a shared folder

<!-- Column 1 -->
## Site Objects

```ascii
SITE OBJECTS

[Site] <------- inherits from ------ [List / Library]

inheritance is broken

[Folder] <------- inherits from ------ [Item / File]

Legend: [Site], [List / Library], [Folder], [Item / File]
```

<!-- Column 2 -->
## Permissions UI Example

[Two screenshots side by side]

Left screenshot highlights:
- Permission tab with "Edit User Permissions" button marked as (2)
- User list with checkbox for "SharePoint SupportTest Members" checked (1)
- Yellow warning: "There are limited access users on this site. This folder has unique permissions."

Right screenshot shows "Permissions > Edit Permissions" dialog with:

Users or Groups  
The permissions of these users or groups will be modified.

Users:  
SharePoint SupportTest Members

Choose Permissions  
Choose the permissions you want these users or groups to have.

Permissions list with checkboxes:
- Full Control - Has full control.
- Design - Can view, add, update, delete, approve, and customize.
- Edit - Can add, edit and delete lists; can view, add, update and delete list items and documents. [checked]
- Contribute - Can view, add, update, and delete list items and documents.
- Read - Can view pages and list items and download documents.
- Restricted View - Can view pages, list items, and documents. Documents can be viewed in the browser but not downloaded.
- View Only - Can view pages, list items, and documents. Document types with server-side file handlers can be viewed in the browser but not downloaded.
- Approve - Can edit and approve pages, list items, and documents.
- Manage Hierarchy - Can create sites and edit pages, list items, and documents.
- Restricted Read - Can view pages and documents, but cannot view historical versions or user permissions.
- Restricted Interfaces for Translation - Can open lists and folders, and use remote interfaces.

Buttons: OK | Cancel

<transcription_image>
**Figure 1: Editing permissions of a shared folder**

```ascii
SITE OBJECTS

[Site] <------- inherits from ------ [List / Library]

inheritance is broken

[Folder] <------- inherits from ------ [Item / File]

Legend: [Site], [List / Library], [Folder], [Item / File]

[PERMISSIONS UI]

+-----------------------------------------------------------+
| [1] SharePoint SupportTest Members [x]                    |
| ...                                                       |
| Warning: There are limited access users on this site.     |
| This folder has unique permissions.                        |
|                                                           |
| [2] Edit User Permissions Button                           |
+-----------------------------------------------------------+

+-----------------------------------------------------------+
| Permissions > Edit Permissions                             |
|                                                           |
| Users or Groups: SharePoint SupportTest Members           |
|                                                           |
| Choose Permissions:                                        |
| [ ] Full Control - Has full control.                      |
| [ ] Design - Can view, add, update, delete, approve, customize. |
| [x] Edit - Can add, edit and delete lists; can view, add, update and delete list items and documents. |
| [ ] Contribute - Can view, add, update, and delete list items and documents. |
| [ ] Read - Can view pages and list items and download documents. |
| [ ] Restricted View - Can view pages, list items, and documents. Documents can be viewed in the browser but not downloaded. |
| [ ] View Only - Can view pages, list items, and documents. Document types with server-side file handlers can be viewed in the browser but not downloaded. |
| [ ] Approve - Can edit and approve pages, list items, and documents. |
| [ ] Manage Hierarchy - Can create sites and edit pages, list items, and documents. |
| [ ] Restricted Read - Can view pages and documents, but cannot view historical versions or user permissions. |
| [ ] Restricted Interfaces for Translation - Can open lists and folders, and use remote interfaces. |
|                                                           |
| [OK] [Cancel]                                             |
+-----------------------------------------------------------+
```
<transcription_notes>
- Data: Users/groups list includes SharePoint SupportTest Members, Owners, Visitors, Approvers, Designers, Excel Services Viewers, Hierarchy Managers, Restricted Readers, Translation Managers.
- Permissions: Only "Edit" permission checked for selected group.
- Colors: Red box highlights "Folder" and "Edit User Permissions" button; blue boxes highlight other site objects.
- ASCII misses: UI details, icons, and exact layout of checkboxes/buttons.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 35 -->

# Removing permissions from a shared folder

<!-- Column 1 -->
## Site Objects

```ascii
SITE OBJECTS PERMISSION INHERITANCE

[Site] <----- inherits from ----- [List / Library]
  (inheritance is broken)

[Folder] <----- inherits from ----- [Item / File]

Legend:
[Site], [List / Library], [Folder], [Item / File] = site objects
```

<!-- Column 2 -->
## Screenshot: Permissions UI and Key Instructions

- A screenshot of a permissions tab UI showing groups with checkboxes
- Red annotation highlights:
  - Checkbox selections for "SharePoint SupportTest Members" and "SharePoint SupportTest Visitors"
  - Red arrow pointing to "SharePoint SupportTest Owners" with text: **Don't remove Owners!**
- Numbered steps:
  1. Checkbox selections on the left side
  2. "Remove User Permissions" button in the ribbon highlighted with a red box and number 2

---

<transcription_image>
**Figure 1: Removing permissions from a shared folder**

```ascii
PERMISSION INHERITANCE DIAGRAM

[Site]                (inherits from)
   ↑
[List / Library]       (inheritance is broken)

[Folder]              (inherits from)
   ↑
[Item / File]

Legend:
[Site], [List / Library], [Folder], [Item / File] = site objects

PERMISSIONS UI (simplified)

+-------------------------------------------------------+
| [1] ☐ Approvers                                       |
| [1] ☐ Designers                                       |
| [x] ☐ Excel Services Viewers                          |
| [1] ☐ Hierarchy Managers                              |
| [1] ☐ Restricted Readers                             |
| [x] ☐ SharePoint SupportTest Members                 |
| [ ] ☐ SharePoint SupportTest Owners <--- Don't remove!|
| [x] ☐ SharePoint SupportTest Visitors                |
| [1] ☐ Translation Managers                            |
+-------------------------------------------------------+

[2] [Remove User Permissions]  (button highlighted)

Legend:
[x] = checked box
[ ] = unchecked box
[1], [2] = step numbers in red circles
```

<transcription_notes>
- Data: Permissions groups include Approvers, Designers, Excel Services Viewers, Hierarchy Managers, Restricted Readers, SharePoint SupportTest Members, SharePoint SupportTest Owners, SharePoint SupportTest Visitors, Translation Managers
- Colors: Blue boxes denote site objects; Red box denotes Folder where inheritance is broken; Red arrow and text emphasize not to remove Owners
- ASCII misses: Exact UI layout, icons, and color highlights
</transcription_notes>
</transcription_image>

---

<!-- PAGE 36 -->

# Restoring permission inheritance

<!-- Column 1 -->
## Site Objects

- Site  
  inherits from → List / Library  
- List / Library  
  inherits from → Folder  
- Folder  
  inherits from → Item / File  

<!-- Column 2 -->
## Permission Levels

- **Limited Access**  
  no access to site  

<!-- Column 3 -->
## Groups

- Limited Access  
  System Group  
  User remains in this group  

<!-- Column 4 -->
## Users

- New User  

<transcription_image>
**Figure 1: Permission inheritance flow and UI for unique permissions**

```ascii
[Restoring permission inheritance]

[Site Objects]               [Permission Levels]            [Groups]                       [Users]
+---------+                  +----------------+             +---------------------+       +------------+
|  Site   | <----------------| Limited Access |<------------| Limited Access       |<------| New User   |
+---------+   inherits from   +----------------+   Limited   | System Group         |       +------------+
     ^                        no access to site           | User remains in this  |
     |                                                    | group                 |
     | inherits from                                       +---------------------+
+-------------+
| List/Library| inherits from
+-------------+
     ^
     | inherits from
+----------+
|  Folder  | inherits from
+----------+
     ^
     | inherits from
+------------+
| Item/File  |
+------------+

[UI Screenshot - highlighted box around "Delete unique permissions"]
Permission tab showing:
- Delete unique permissions
- Grant Permissions
- Edit User Permissions
- Remove User Permissions
- Check Permissions

Warning message:
"This document has unique permissions."
```

<transcription_notes>
- Data: No numerical data present
- Colors: Blue - site objects and users; Red - permission levels and groups (Limited Access emphasis)
- ASCII misses: UI screenshot details simplified to text description
</transcription_notes>

---

<!-- PAGE 37 -->

# Mastering SharePoint Permissions

## Tips & Tricks for SharePoint permissions

<transcription_image>
**Figure 1: Raccoon character with question mark**

```ascii
[Graphic: Raccoon character inside a circle]

       _____________ 
      /             \
     |   [RACCOON]   |  <-- Character with eyes, ears, striped tail
     |      ?        |  <-- Blue question mark on chest
      \_____________/
           |   |
         [BASE]  <-- Green base platform

Legend: [RACCOON]=Character, [BASE]=Ground platform
```

<transcription_notes>
- Colors: Blue = question mark; Green = base platform; Grey = raccoon body; Light blue circle around character
- No data values to extract
- ASCII misses: detailed facial features, stripes, shading
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 38 -->

# Tips & Tricks for SharePoint permissions

- How can I remove a user entirely from a site?  
  - As Admin: Site Settings > People and groups > In Browser URL bar, replace  
    `.../15/people.aspx?MembershipGroupId=8` with `...GroupId=0`, press ENTER, then select user and choose Actions > Delete Users from Site Collection  
  - As Owner: Open Ticket and ask for removal of user (add site URL + user name / email)  
- How can I change the default group of my site (Default = Members)?  
  - Site Settings > People and groups > click on group on left (or see in More...) > Settings > Make Default Group  
- How can I delete a group?  
  - Site Settings > People and groups > click on group on left (or see in More...) > Settings > Group Settings > Delete (att bottom of page)

<transcription_page_footer> Page [unclear] | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 39 -->

# Tips & Tricks for SharePoint permissions

- I have removed a group from "Site permissions", how can I get it back?  
  - Click "Grant Permissions" > Enter group name > Click "Show Options" > Select Permission Level > Share  
- How can I prevent users from downloading files or opening them in Office Desktop Apps?  
  - Use "View Only" permission level or copy and modify it  
- How can I prevent users from syncing files?  
  - Entire Site: Site Settings > Search and Offline Availability > Offline Client Availability  
  - Per Library: Library settings > Advanced Settings > Offline Client Availability  

<transcription_page_footer> Page 1 | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 40 -->

# Tips & Tricks for SharePoint permissions

- How can I prevent users from sharing files?  
  - Classic: Site Settings > Site Permissions > Access Request Settings > Allow members to share the site and individual files and folders  
  - Modern: Cogwheel icon > Site permissions > Change how members can share > Select last option

<transcription_image>
**Figure 1: Screenshots showing settings to prevent users from sharing files**

```ascii
[Access Requests Settings]  
+----------------------------------------------------------+  
| Access Requests Settings                                  |  
| Choose who can request access                             |  
| or invite others to this site.                            |  
|                                                          |  
| [ ] Allow members to share the site and individual files |  
|     and folders.           <-- [A]                        |  
| [ ] Allow members to invite others to the site members   |  
|     group, SharePoi...                                     |  
|                                                          |  
| [x] Allow access requests                                 |  
| Select who will receive all access requests on this site |  
| ( ) SharePoint SupportTest Owners                         |  
| ( ) [e-mail address]                                      |  
| Only members of the SharePoint SupportTest Owners group  |  
| can acc...                                               |  
| Include a custom message to users who see access request |  
| page                                                    |  
+----------------------------------------------------------+  

[Settings]  
+-------------------------+  
| SharePoint               |  
| Add a page               |  
| Add an app               |  
| Site contents           |  
| Site information        |  
| [Site permissions]      <-- [B]  
| Site usage              |  
| Change the look         |  
| Site designs            |  
+-------------------------+  

[Permissions]  
+-------------------------------------------------+  
| Manage site permissions or invite others to    |  
| collaborate                                     |  
| [Invite people] (button)                        |  
|                                                 |  
| Site owners                                     |  
| Site members                                    |  
| Site visitors                                   |  
|                                                 |  
| Site Sharing                                    |  
| [Change how members can share]  <-- [C]         |  
+-------------------------------------------------+  

[Site sharing settings]  
+-------------------------------------------------+  
| Control how things in this site can be shared   |  
| and how request access works.                    |  
|                                                 |  
| Sharing permissions                              |  
| ( ) Site owners and members can share files,    |  
|     folders, and the site. People with Edit      |  
|     permissions can share files and folders.    |  
|                                                 |  
| ( ) Site owners and members, and people          |  
|     with Edit permissions can share files and    |  
|     folders, but only site owners can share the  |  
|     site.                                        |  
|                                                 |  
| (●) Only site owners can share files, folders,  |  
|     and the site.                                |  
+-------------------------------------------------+  
```

<transcription_notes>
- Red boxes highlight key settings:  
  [A] "Allow members to share the site and individual files and folders" (unchecked)  
  [B] "Site permissions" menu item  
  [C] "Change how members can share" link  
- In "Site sharing settings," the selected option is "Only site owners can share files, folders, and the site."
- The screenshots illustrate both Classic and Modern SharePoint UI settings for controlling file sharing permissions.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 41 -->

# Tips & Tricks for SharePoint permissions

- I invited users to a custom group with permissions on site but users get "Access Denied" when accessing the site.  
  - A) Add group to permissions of "Site Pages":  
    Site Contents > Site Pages > DotDotDot Icon "..." > Settings > Permissions for this document library > Grant Permissions > Enter group name, choose permissions > Share  
  - B) Restore Permission Inheritance of "Site Pages":  
    Site Contents > Site Pages > DotDotDot Icon "..." > Settings > Permissions for this document library > Delete unique permissions

<transcription_image>
**Figure 1: SharePoint permissions UI walkthrough**

```ascii
[Site Pages] --(click DotDotDot Icon "...")-->
    [Context Menu]
    - Remove
    - Settings  [highlighted]
    - Details

[Settings Page]
General Settings                      Permissions and Management
- List name, description and navigation    - Delete this document library
- Versioning settings                       - Permissions for this document library  [highlighted]
- Advanced settings                         - Manage files which have no checked in version

[Permissions Tab]
[BROWSE] [PERMISSIONS]
[Delete unique permissions] [Grant Permissions] [Edit User permissions] [Remove User Permissions] [Check Permissions]
  ^                          ^
  |                          |
[highlighted]            [highlighted]
```

<transcription_notes>
- Data: N/A (UI screenshots with highlighted elements)
- Colors: Red boxes highlight key menu items/buttons
- ASCII misses: Visual UI layout and icons simplified; no exact button graphics
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 42 -->

# Tips & Tricks for SharePoint permissions

- I deleted a group but the former members still have access to the site.  
  - That's by design. Remove those members from "All Members" group (the one with GroupId=0, see first question)  
  - Next time: First remove all users from the group. Then you can delete the group itself.

- Is there a minimal permission level setting that allows users to see the site but not the files?  
  - Yes: View pages + Browse User Information + Use Remote Interfaces + Open

<transcription_image>
**Figure 1: SharePoint minimal permissions checkboxes**

```ascii
[PROCESS] SharePoint Permission Options
+-------------------------------------------+
| [x] View Pages       - View pages in a Web site.                   |
| [ ] Enumerate Permissions - Enumerate permissions on the Web site,|
|                            list, folder, document, or list item.   |
| [x] Browse User Information - View information about users of the  |
|                               Web site.                            |
| [ ] Manage Alerts     - Manage alerts for all users of the Web site.|
| [x] Use Remote Interfaces - Use SOAP, Web DAV, the Client Object   |
|                            Model or SharePoint Designer interfaces |
|                            to access the Web site.                |
| [ ] Use Client Integration Features - Use features which launch    |
|                                       client applications. Without |
|                                       this permission, users will |
|                                       have to work on documents   |
|                                       locally and upload their    |
|                                       changes.                    |
| [x] Open             - Allows users to open a Web site, list, or  |
|                        folder in order to access items inside that|
|                        container.                                |
+-------------------------------------------+
Legend: [x]=checked [ ]=unchecked
```

<transcription_notes>
- Data: Permissions with checkboxes: View Pages, Browse User Information, Use Remote Interfaces, Open are checked; Enumerate Permissions, Manage Alerts, Use Client Integration Features are unchecked.
- Colors: Green boxes in original highlight checked options.
- ASCII misses: Visual checkbox styling and green highlight boxes.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 43 -->

```markdown
# Mastering SharePoint Permissions

## Other groups in Office 356

<!-- Decorative: mascot graphic, company logo -->

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>
```

---

<!-- PAGE 44 -->

```markdown
## Other groups in Office 365

- Distribution Group
  - Sending email to a specified audience
  - Filtering SharePoint content
- Security Group
  - For controlling access to objects On-Premise and in the Cloud
- Mail-enabled Security Group
  - Combination of a Security and a Distribution Group
- Office 365 Group
  - Cloud-only, has mailbox and calendar
  - Unified object to control access to Teams, SharePoint, Planner, PowerBI
```

---

<!-- PAGE 45 -->

# How to access Groups in the Cloud

- Go to [https://portal.azure.com/](https://portal.azure.com/) > Azure Active Directory > Groups

<transcription_image>
**Figure 1: Steps to access Groups in Azure Portal**

```ascii
[AZURE PORTAL HOME PAGE]
+------------------------------------------------------------+
| Address bar: portal.azure.com/#home (1)                    |
|                                                            |
| Azure services:                                            |
|  + Create a resource                                       |
|  [Azure Active Directory] (2)  Groups  Management groups  |
|  All resources  Resource groups  Virtual machines         |
|  App Services  Storage accounts  More services            |
+------------------------------------------------------------+

[AZURE ACTIVE DIRECTORY PANEL]
+--------------------------------------+
| Overview                             |
| Getting started                     |
| Diagnose and solve problems         |
| Manage:                            |
|  Users                            |
|  [Groups] (3)                      |
|  Organizational relationships     |
|  Roles and administrators         |
|  Enterprise applications          |
|  Devices                         |
|  App registrations               |
|  Identity Governance             |
|  Application proxy              |
|  Licenses                      |
|  Azure AD Connect             |
+--------------------------------------+

[GROUPS LIST PANEL]
+--------------------------------------------------------------------------------------------------+
| Groups | All groups                                                                              |
|-------------------------------------------------------------------------------------------------|
| [ ] Name                | Object Id               | Group Type | Membership Type | Email             | Source          |
|-------------------------------------------------------------------------------------------------|
| [ ] z_azu_vsts_cloudcor...| 61df177f-03a04-bc79... | Security   | Assigned        |                   | Windows server AD |
| [ ] "Block Chain" in me... | fb0ea977-2481-45e1... | Office     | Assigned        | BlockChaininmeters@grou... | Cloud         |
| [ ] "ED" Controls         | ecfcb50c-5530-4923... | Office     | Assigned        | EDControls@groups.vatten... | Cloud         |
| [ ] "Klassenfahrt"        | 39245904-6200-4628... | Office     | Assigned        | Klassenfahrt@groups.vatte... | Cloud         |
| [ ] "Neu bei SNB" Tea...  | f753db53-0fec-4b05... | Office     | Assigned        | NeubeiSNBTeamTalk@grou... | Cloud         |
| [ ] 1WOL-Circle NW        | 90cbd8af-fe19-4380... | Office     | Assigned        | 1WOL-CircleNW@groups.vat... | Cloud         |
| [ ] #Eichrecht HW         | 2832a572-b7c5-4630... | Office     | Assigned        | EichrechtHW@groups.vatt... | Cloud         |
| [ ] #Site Inspector Tea...| cbe7a782-0c5e-466a... | Office     | Assigned        | SiteInspectorTeamspage@... | Cloud         |
| ...                      | ...                     | ...        | ...             | ...                 | ...             |
+--------------------------------------------------------------------------------------------------+
```

<transcription_notes>
- Data: URL: https://portal.azure.com/; Steps: 1=Go to portal URL; 2=Click Azure Active Directory; 3=Click Groups
- Groups table columns: Name, Object Id, Group Type, Membership Type, Email, Source
- Examples of group names and sources shown (Office groups mostly, one Windows server AD)
- Numbers and text in Object Ids partially shown
- Highlight boxes around steps 1, 2, 3 in red
</transcription_notes>
</transcription_image>

---

<!-- PAGE 46 -->

# Nesting possibilities

- Distribution Group  
  - can contain another Distribution Group
- Security Group  
  - can contain another Security Group
- Mail-enabled Security Group  
  - can contain both, Security and Distribution Groups
- Office 365 Group  
  - cannot be nested, Microsoft is working on this  
  - If you try adding an Office 365 Group in Teams, the members will be copied to the associated Office 365 Group of that Team
- SharePoint Group  
  - cannot be nested

from Goran Husman:  
Understanding Office 365 Permissions

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 47 -->

# What is an Office 365 Group?

An Office 365 group is an object in the Microsoft cloud (Azure) for managing the membership and access to different apps in Office 365.

<transcription_image>
**Figure 1: Office 365 Group Components and Connected Apps**

```ascii
                  +-----------------------+
                  |     Office 365 Group   |
                  |  +-----------------+  |
                  |  |    Owners       |  |
                  |  |    Members      |  |
                  |  |   EXT Accounts  |  |
                  |  +-----------------+  |
                  +-----------------------+
                     /     |      |      \
                    /      |      |       \
                   /       |      |        \
                  /        |      |         \
                 •         •      •          •
                 |         |      |          |
  Teams          | SharePoint     | Outlook   | Power BI     | Planner
 Conversations   | Files          | Mailbox + | Dashboards   | Plans
 (T)            | (S)            | Calendar  | (Power BI)   | (Planner)
```

Legend:
- [•] = Connection node
- (T) = Teams
- (S) = SharePoint
- (Power BI) = Power BI app
- (Planner) = Planner app

<transcription_notes>
- The Office 365 Group contains three membership types: Owners, Members, EXT Accounts.
- Connected applications are Teams (Conversations), SharePoint (Files), Outlook (Mailbox + Calendar), Power BI (Dashboards), Planner (Plans).
- Colors in original: Blue for Office 365 Group and connected apps; Green for Planner.
- Icons for each app are shown but cannot be represented in ASCII.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 48 -->

# Caution: Deleting the Office 365 Group deletes everything!

<transcription_image>
**Figure 1: Office 365 Group Deletion Impact**

```ascii
                     [Office 365 Group]
                     +------------------+
                     | Owners           |  [TRASH]
                     | Members          |
                     | EXT Accounts     |
                     +------------------+
                  /      |        |       \
                 /       |        |        \
                /        |        |         \
               ●---------●--------●----------●
               |         |        |          |
[Teams  T]  [SharePoint S]  [Planner]  [Outlook O]  [Power BI]
Conversations Files       Plans       Mailbox + Calendar Dashboards
    [X]         [TRASH]   [✓]  [TRASH]      [TRASH]       [TRASH]

Legend:
● = connection node
[X] = delete Teams Conversations (cross mark)
[✓] = Planner Plans safe icon (green)
[TRASH] = deletion icon (red trash bin)
```

<transcription_notes>
- Data: N/A (diagram)
- Colors: Blue = Office 365 services and group; Red = Deletion indicated; Green = Planner Plans safe icon
- ASCII misses: logos and color shades, trash bin icons, check mark icon
</transcription_notes>
</transcription_image>

Deleting a Team, a SharePoint site, a Planner or a PowerBI workspace will delete the whole Office 365 group with all connections.

---

<transcription_page_footer> Confidentiality: C2 - Internal | Vattenfall </transcription_page_footer>

---

<!-- PAGE 49 -->

# How to find the Office 365 Group settings

- From Teams: In channel "General" > ... > Open in SharePoint  
- From SharePoint: In left Navigation > Conversations

<transcription_image>
**Figure 1: Steps to find Office 365 Group settings from Teams and SharePoint**

```ascii
[TEAMS WINDOW]                                         [SHAREPOINT NAVIGATION]
+--------------------------+                          +------------------------+
| Your teams               |                          | SharePoint             |
|  +---------------------+ |                          |  Home                  |
|  | 1 General           | |---> (arrow 1) ------------>  3 Conversations   |        [3]
|  +---------------------+ |                          |  Documents             |
|                          |                          |  Notebook              |
|  +---------------------+ |                          +------------------------+
|                          |                          [PROCESS] Open in SharePoint [2]
+--------------------------+

[OUTLOOK MAIL WINDOW]
+-------------------------------------------------------------------------+
| SharePoint Tips & Tricks SPTNT                                           |
| Private group · 3 members                                                |
| [Email] Send email  <--- Email [label]                                 |
| [Calendar] (calendar icon)  <--- Calendar [label]                      |
| ... (more options)                                                        |
|      +-------------------+                                               |
|      | Notebook          |                                               |
|      | Planner           |                                               |
|      | Site              |                                               |
|      | 4 Settings        |  <--- (arrow 4) ----------------------------> |
|      +-------------------+                                               |
|                                                                         |
+-------------------------------------------------------------------------+

[GROUP SETTINGS PANEL]
+-------------------------------------------------------------+
| Group Settings                                             |
| SharePoint Tips & Tricks SPTNT                              |
| Manage group email                                         |
| Choose which group messages to receive in your inbox       |
|  o Follow in inbox                                          |
|      • Receive all email and events                         |
|  o Stop following in inbox                                  |
|      o Receive only replies to you and group events        |
|      o Receive only replies to you                          |
|      o Don't receive any group messages                     |
|                                                             |
|  5 Edit group  <--- (arrow 5)                               |
|  Change the settings for this group                         |
|                                                             |
|  Leave group                                                |
+-------------------------------------------------------------+
```

<transcription_notes>
- Numbered steps: 
  1 = Click "General" channel in Teams  
  2 = Click "Open in SharePoint" button  
  3 = Select "Conversations" in SharePoint left navigation  
  4 = Click "Settings" from dropdown in Outlook group page  
  5 = Click "Edit group" in Group Settings panel  
- Labels: Email and Calendar icons indicated  
- Application windows shown: Teams, SharePoint, Outlook, Group Settings  
- Arrows indicate navigation flow across apps and menus  
</transcription_notes>
</transcription_image>

---

<!-- PAGE 50 -->

# How to find the Office 365 Group settings

<transcription_image>
**Figure 1: Office 365 Group Settings Window and Key Options Highlight**

```ascii
[OFFICE 365 GROUP SETTINGS WINDOW]

+-----------------------------------------------------------+
| Edit group                                                |
|                                                           |
| Working together on a project or a                        |
| shared goal? Create a group to give                       |
| your team a space for                                     |
| conversations, shared files,                             |
| scheduling events, and more.                              |
|                                                           |
|   (Illustration of 4 people icons)                       |
|                                                           |
| Group name                                               |
| SharePoint Tips & Tricks SPTNT                           |
| Group email address                                      |
| SPTNT@groups.vattenfall.com                             |
|                                                           |
| Description                                             |
| SharePoint Tips & Tricks                                 |
|                                                           |
| Settings                                                |
| Privacy                                                 |
| Private - Only approved members can see what's inside  |
|                                                           |
| Language for group-related notifications                |
| English (United States)                                  |
|                                                           |
| [ ] Let people outside the organisation email the group  |  <-- [Checkbox 1]
|                                                           |
| [ ] Send all group conversations and events to members'   |  <-- [Checkbox 2]
|     inboxes. They can stop following this group later if  |
|     they want to.                                         |
|                                                           |
|  [Save]   [Discard]                                  [Delete group] |
+-----------------------------------------------------------+

Inset zoom on two checkboxes:

[ ] Let people outside the organisation email the group

[ ] Send all group conversations and events to members' inboxes. They can stop following this group later if they want to.

--> This makes the Office 365 Group behave like a Distribution Group
```

<transcription_notes>
- Data: Group name: "SharePoint Tips & Tricks SPTNT"
- Email: SPTNT@groups.vattenfall.com
- Settings: Privacy set to Private - Only approved members can see what's inside
- Language: English (United States)
- Two key checkboxes unchecked, highlighted in red box
- Red underline under second checkbox text in zoom callout
- Red text note: "This makes the Office 365 Group behave like a Distribution Group"
- Colors: Blue = headings, Red = emphasis box and text
- ASCII misses: Illustration of people simplified as labeled "4 people icons"
</transcription_notes>
</transcription_image>

---

<!-- PAGE 51 -->

# The Office 365 Group in modern sites

- Modern SharePoint sites are "Office 365 Group connected" by default  
- New members will be added to the Office 365 Group  
- SharePoint Groups and Permissions are **not replaced** by Office 365 Group  
  - The Office 365 Group roles (Owners & Members) are nested in the classic SharePoint Groups  
- The Office 365 Group does not support all SharePoint Permissions  
  - No "Read Only" = Visitor role  
  - Members can have only "Edit" = Members or "Full Control" = Admins  
  - Owners group is empty by default  
- Classic SharePoint groups and permissions will have to be used in parallel  
  - Users might have access to the SharePoint but not to Teams, Planner, PowerBI  
  - Permissions defined by the Office 365 Group role and the SharePoint Groups might differ, even be contradicting. **That's a challenge for site owners.**

<transcription_page_footer> Page [unclear] | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 52 -->

# Inviting Members

<!-- Column 1 -->

## Classic

- A) Using the "Share" button on the classic Homepage  
- B) Adding users to groups from Site Settings

<transcription_image>
**Figure 1: Classic method screenshots for inviting members**

```ascii
[SCREENSHOT - CLASSIC HOMEPAGE]

+------------------------------------------------------------+
| People and Groups > SharePoint Su...                        |
|  New ▼   Actions ▼   Settings ▼                             |
|  (empty list with text: "There are no items to show...")   |
+------------------------------------------------------------+

[SCREENSHOT - SHARE BUTTON HIGHLIGHTED]

+------------------------------+
|  🔔   ?     Held Karsten (YI) |
| ---------------------------- |
|  [ SHARE ] [ FOLLOW ] [ EDIT ]|
|  Search this site ▼           |
+------------------------------+

[SCREENSHOT - SHARE DIALOG]

+------------------------------------------+
| Share 'My SharePoint Site'                |
| Invite people                            |
| Shared with                             |
| +------------------------------------+  |
| | Enter names or email addresses.     |  |
| +------------------------------------+  |
| Include a personal message with... (opt) |
| [ ] Send an email invitation             |
| [ Share ] [ Cancel ]                      |
+------------------------------------------+
```

<transcription_notes>
- Data: No numeric data
- Colors: Red boxes highlight "New" menu, "Share" button, and input fields
- ASCII misses: Visual UI elements and images (profile pictures)
</transcription_notes>
</transcription_image>

<!-- Column 2 -->

## Modern

- A) Office 365 Group: Using the "Members" link on the Homepage  
- B) SharePoint Group: Using Site Permissions > Advanced Permission Settings

<transcription_image>
**Figure 2: Modern method screenshots for inviting members**

```ascii
[SCREENSHOT - SITE PERMISSIONS MENU]

+-------------------------------+
| Settings                      |
| ----------------------------- |
| SharePoint                   |
|  Add a page                  |
|  Add an app                  |
|  Site contents               |
|  Site information            |
|  [ Site permissions ]        |  <-- [PROCESS]
|  Site usage                  |
|  Change the look             |
|  Site designs                |
+-------------------------------+

[SCREENSHOT - PERMISSIONS DIALOG]

+-------------------------------------------+
| Permissions                                |
| Manage site permissions or invite others  |
| to collaborate                             |
| [ Invite people ] [green button]           |
| - Site owners                              |
| - Site members                             |
| - Site visitors                            |
| Site Sharing                               |
| Change how members can share               |
| ...                                       |
| [ Advanced permissions settings ]          |  <-- [PROCESS]
+-------------------------------------------+

[SCREENSHOT - GROUP MEMBERSHIP]

+-------------------------------------+
| Held Karsten (YI...)                 |
| ★ Following                        |
| [ 3 members ]                      |  <-- [PROCESS]
+-------------------------------------+

[SCREENSHOT - ADD MEMBERS DIALOG]

+-------------------------------------+
| Group membership                    |
| 4 members                         |
| [ Add members ] [green button]     |
| Winkler Torsten (YIOHW) Member     |
| Held Karsten (YINCM) ext Owner     |
| Salur Rafet (YINCM) ext Member     |
| Vichare Rohan (YINCM) ext Owner    |
+-------------------------------------+
```

<transcription_notes>
- Data: Group membership total 4 members, 3 members shown on card, buttons "Invite people" and "Add members" in green
- Colors: Red boxes highlight "Site permissions," "Advanced permissions settings," and "3 members" links
- ASCII misses: Profile pictures and exact UI layout
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 53 -->

# Whenever you create a new Team you will get

<transcription_image>
**Figure 1: Structure and components received when creating a new Team**

```ascii
[1] Team
┌────────────────────────────────────────────┐
│ Channel "General"                           │
│ Tab "Conversations"                         │
│ Tab "Files"                                │
│ Tab "Wiki"                                 │
│                                            │
│ Team Members                               │
│   Owners                                   │ <------┐
│   Members                                  │ <------┐
│   Guests                                   │ <------┐
└────────────────────────────────────────────┘
         |           |              |
         |           |              |
         V           V              V

[2] Office 365 Group
┌────────────────────────────────────────────┐
│ Owners                                    │ ──────> [3] SharePoint Site > Site Admins
│ Members                                   │ ──────> [3] SharePoint Site > Site Members > Office 365 Group
│ EXT Accounts                              │ ──────> [3] SharePoint Site > Site Members > Office 365 Group
└────────────────────────────────────────────┘

[3] SharePoint Site
┌────────────────────────────────────────────┐
│ Site Admins                                │
│                                            │
│ Site Members                               │
│   Office 365 Group                         │
│                                            │
│ Site Owners                                │
│                                            │
│ Site Visitors                              │
└────────────────────────────────────────────┘

(pending) Planner
  can be added later (dashed box, grey)
```

Legend:  
[1]=Team [2]=Office 365 Group [3]=SharePoint Site

Orange arrows show membership links from Team Members to Office 365 Group, and from Office 365 Group to SharePoint Site roles.

Red text (below diagram): "This is called an 'Office 356 group connected site' or 'Modern Team Site'"

```
<transcription_notes>
- Data: Team has 1 Channel "General"; 3 Tabs: "Conversations", "Files", "Wiki".
- Team Members: Owners, Members, Guests.
- Office 365 Group roles: Owners, Members, EXT Accounts.
- SharePoint Site roles: Site Admins, Site Members (includes Office 365 Group), Site Owners, Site Visitors.
- Planner can be added later (dashed, grey box).
- Arrows in orange represent membership relationships.
- Red text emphasizes naming: "Office 356 group connected site" or "Modern Team Site".
- Colors: Blue for Team and Office 365 Group, Teal for SharePoint Site, Grey for Site Admins, Light blue highlight around "Office 365 Group" within Site Members.
- Some small text at bottom left: "Confidentiality: C2 - Internal".
- Logo: VATTENFALL with blue and yellow icon.
</transcription_notes>
</transcription_image>

---

<!-- PAGE 54 -->

# The Office 365 Group in modern sites

- SharePoint Group is  
  - A "SharePoint" only feature  
  - used to grant access to a single site collection  
  - used ot grant access to only SharePoint and nothing else  
  - used to manage permissions in SharePoint On Premise  
- Office 365 Group is  
  - A new type of group that only works in the cloud  
  - used to manage permissions in Microsoft Teams  
  - also used to manage permissions for SharePoint, Planner, PowerBI  
  - will be automatically created when you create a Team, a modern SharePoint site  

<transcription_page_footer> Page 1 | VATTENFALL </transcription_page_footer>

---

<!-- PAGE 55 -->

# [No title on page]

<!-- Decorative: VATTENFALL logo (center, circle: yellow/blue) -->

Page contains no main body text; slide is visually blank except for footers and a centered company logo.

<transcription_image>
**Figure 1: Blank slide with footers and centered VATTENFALL logo**

```ascii
[PAGE - mostly blank]

                           [LOGO - VATTENFALL]  (center)
                            
Bottom-left:  Confidentiality: C2 - Internal
Bottom-center: VATTENFALL  [circle logo: yellow / blue]
Bottom-right: Confidentiality – Critical (C4), High (C3), Medium (C2), None (C1)  55
```

<transcription_notes>
- Data: No chart or tabular data present.
- Text values transcribed exactly as visible:
  - Left footer: "Confidentiality: C2 - Internal"
  - Center (logo text): "VATTENFALL"
  - Right footer: "Confidentiality – Critical (C4), High (C3), Medium (C2), None (C1) 55"
- Colors: yellow / blue = logo circle (visual; decorative).
- ASCII misses: exact logo graphic, fonts, and precise positioning.
</transcription_notes>
</transcription_image>

<transcription_page_footer> Confidentiality: C2 - Internal  |  VATTENFALL (logo center)  |  Confidentiality – Critical (C4), High (C3), Medium (C2), None (C1) 55 </transcription_page_footer>

---

