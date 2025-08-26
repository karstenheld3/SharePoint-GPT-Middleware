# SharePoint-GPT-Middleware Software Requirements Specification (SRS)

## 1. Introduction

SharePoint-GPT consists of 3 parts:
- SharePoint GPT Web Parts (SPGPTWP)
- SharePoint GPT Middleware (SPGPTMW)
- Azure Open AI Service (AOIS)

### 1.1 Purpose
In this document we describe the requirements for the SharePoint GPT Middleware. It serves as a bridge between the SharePoint GPT Web Parts and the Azure Open AI Service so that the Azure Open AI Service is not exposed to anything but the SharePoint GPT Middleware.

### 1.2 Scope
Features:
- Access to Azure Open AI Service via Open AI API Bridge
- SharePoint Search Endpoints /alive, /describe, /query, /query2, /queryrt, /queryrt2
- Exposes all endpoints as MCP servers

### 1.3 Definitions and Acronyms
| Term | Definition |
|------|------------|
| API | Application Programming Interface |
| UI  | User Interface |
| SPGPTWP | SharePoint GPT Web Parts |
| SPGPTMW | SharePoint GPT Middleware |
| AOIS | Azure Open AI Service |

---

## 2. Overall Description

### 2.1 Product Perspective
_Describe how this product fits into a larger system or whether it's standalone._

### 2.2 Product Functions
_Summarize the major functions the system will perform._

### 2.3 User Classes and Characteristics
_List different types of users and their roles in the system._

### 2.4 Operating Environment
_Specify the hardware, software, and other technical environments._

---

## 3. Functional Requirements

### 3.1 Authentication
- **FR1**: The system shall allow users to register with an email and password.
- **FR2**: The system shall allow users to log in and out securely.

### 3.2 Core Features
- **FR3**: [Feature Name]: Description of the functionality.
- **FR4**: [Feature Name]: Description of the functionality.

_Note: Use "FR" numbering to uniquely identify functional requirements._

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements
- **NFR1**: The system shall respond to user actions within 500 milliseconds.

### 4.2 Security Requirements
- **NFR2**: All passwords shall be encrypted using bcrypt.

### 4.3 Usability Requirements
- **NFR3**: The UI shall be compliant with WCAG 2.1 AA accessibility standards.

---

## 5. Assumptions and Dependencies

- This software assumes that all users have access to a stable internet connection.
- Integration with external services (e.g., payment gateways) depends on their API availability.

---

## 6. Future Enhancements

_List any features planned for future releases beyond the current scope._

- Multi-language support
- Offline mode
- Advanced analytics dashboard

---

## 7. Appendix

_Include additional supporting information, diagrams, glossary, etc., if necessary._

