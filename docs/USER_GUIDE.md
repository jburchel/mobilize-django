# Mobilize CRM User Guide

**Version:** 1.0  
**Last Updated:** February 2025

Welcome to Mobilize CRM, a comprehensive Customer Relationship Management system designed specifically for non-profit organizations, churches, and missionary organizations to manage contacts, communications, and relationships.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Contact Management](#contact-management)
4. [Church Management](#church-management)
5. [Pipeline Management](#pipeline-management)
6. [Task Management](#task-management)
7. [Email Integration (Gmail)](#email-integration-gmail)
8. [Calendar Integration](#calendar-integration)
9. [Reports and Analytics](#reports-and-analytics)
10. [User Settings and Preferences](#user-settings-and-preferences)
11. [Administrative Features](#administrative-features)
12. [Troubleshooting](#troubleshooting)
13. [Frequently Asked Questions](#frequently-asked-questions)

---

## Getting Started

### Initial Login

Mobilize CRM uses Google OAuth for authentication, ensuring secure access while leveraging your existing Google account.

#### First-Time Login Steps:

1. **Navigate to Mobilize CRM**: Open your web browser and go to your organization's Mobilize CRM URL
2. **Click "Sign in with Google"**: You'll be redirected to Google's authentication page
3. **Authorize Permissions**: Grant the necessary permissions for:
   - Basic profile information (email, name)
   - Gmail access (for email integration)
   - Google Contacts access (for contact synchronization)
   - Google Calendar access (for calendar integration)
4. **Complete Profile Setup**: After first login, you'll be prompted to complete your profile

> **💡 Tip**: Mobilize CRM automatically creates a Person record for you in the system, linking your user account to the CRM data.

#### Understanding User Roles

Mobilize CRM has four distinct user roles with different levels of access:

| Role | Access Level | Key Permissions |
|------|-------------|----------------|
| **Super Admin** | System-wide access | All data, all offices, system configuration |
| **Office Admin** | Office-wide access | All data within assigned office(s) |
| **Standard User** | Personal + Office data | Own contacts, office churches, assigned tasks |
| **Limited User** | View-only access | View permissions only, no editing |

> **⚠️ Note**: Your role is assigned by your system administrator and determines what features and data you can access.

### Navigation Overview

The main navigation is located in the top menu bar and includes:

- **Dashboard**: Overview of key metrics and recent activity
- **People**: Individual contact management
- **Churches**: Organizational contact management
- **Tasks**: Task assignment and tracking
- **Communications**: Email history and templates
- **Pipeline**: Relationship progress tracking
- **Reports**: Data export and analytics
- **Settings**: Personal and system preferences

---

## Dashboard Overview

The Dashboard is your central hub, providing a comprehensive view of your CRM data and activities.

### Key Dashboard Sections

#### 1. Summary Metrics
- **People Count**: Total individuals in your accessible database
- **Churches Count**: Total organizations in your accessible database
- **Pending Tasks**: Tasks assigned to you that need attention
- **Overdue Tasks**: Past-due tasks requiring immediate action

#### 2. Pipeline Distribution
Visual representation of where your contacts are in their relationship journey:

**People Pipeline Stages:**
- **Promotion**: Initial awareness and interest
- **Information**: Sharing detailed information
- **Invitation**: Formal invitation to participate
- **Confirmation**: Commitment confirmation
- **Automation**: Ongoing relationship management

**Church Pipeline Stages:**
- All the above stages plus:
- **EN42**: Enhanced engagement level (church-specific)

#### 3. Recent Activity Timeline
A 7-day activity chart showing:
- New people added
- Tasks completed
- Communications sent

#### 4. Quick Actions
- **Add New Person**: Quickly create individual contacts
- **Add New Church**: Create organizational contacts
- **Create Task**: Assign new tasks
- **Send Email**: Compose and send communications

### Dashboard Customization

#### Widget Management
You can customize your dashboard by:
1. **Enabling/Disabling Widgets**: Click the settings icon to toggle widgets on/off
2. **Reordering Widgets**: Drag and drop widgets to rearrange their position
3. **Resizing Widgets**: Adjust widget column spans (1-4 columns)
4. **Resetting Layout**: Return to default configuration

#### View Modes (Admin Users Only)
- **Default View**: Shows data based on your role and permissions
- **My Only**: Shows only data you created or are assigned to
- **All Data**: Shows all organizational data (Super Admin only)

> **💡 Tip**: Dashboard data is cached for performance. Metrics refresh every hour automatically.

---

## Contact Management

Mobilize CRM uses a hierarchical contact system with a base **Contact** model that extends into specific **Person** and **Church** records.

### Understanding the Contact Structure

#### Base Contact Fields (Common to People and Churches):
- **Basic Information**: First/last name, email, phone
- **Address**: Street, city, state, zip code, country
- **Priority Level**: Low, Medium, High
- **Status**: Active, Inactive
- **Notes**: General observations and comments
- **Tags**: Categorization labels (JSON field)
- **Custom Fields**: Organization-specific data (JSON field)

### Managing People (Individuals)

#### Adding a New Person

1. **Navigate to People**: Click "People" in the main navigation
2. **Click "Add Person"**: Use the prominent add button
3. **Fill Required Fields**:
   - First Name (recommended)
   - Last Name (recommended)
   - Email (unique if provided)
   - Phone Number
4. **Complete Additional Information**:
   - **Personal Details**: Title, preferred name, birthday, anniversary
   - **Marital Status**: Single, married, divorced, widowed, engaged
   - **Spouse Information**: Names if married
   - **Professional Details**: Occupation, organization/employer
   - **Church Relationship**: Primary church affiliation and role
   - **Social Media**: LinkedIn, Facebook, Twitter, Instagram URLs
   - **Mission Information**: Service interests and location preferences

#### Person-Specific Features

**Church Memberships**: People can be associated with multiple churches through the `ChurchMembership` model:
- **Roles**: Senior Pastor, Associate Pastor, Elder, Deacon, Member, etc.
- **Primary Contact**: Designate someone as the main contact for a church
- **Status**: Active, inactive, or former membership
- **Date Ranges**: Track when relationships started/ended

**Address Management**: Full address support with formatted display
**Language Support**: Multiple languages stored in JSON format
**Google Integration**: Automatic syncing with Google Contacts when enabled

#### Viewing and Editing People

**List View Features**:
- **Search**: Real-time search by name, email, or phone
- **Filtering**: By priority, status, church affiliation, pipeline stage
- **Sorting**: By name, creation date, last contact date
- **Bulk Actions**: Mass updates to selected contacts

**Detail View Features**:
- **Complete Profile**: All contact information in organized sections
- **Communication History**: All emails, calls, and interactions
- **Task History**: Associated tasks and their status
- **Pipeline Progress**: Current stage and movement history
- **Church Relationships**: All church affiliations and roles

#### Best Practices for People Management

✅ **Do:**
- Keep email addresses unique and accurate for Gmail sync
- Use the notes field for context and relationship details
- Regularly update pipeline stages to reflect relationship progress
- Tag contacts for easy categorization and filtering
- Link people to their primary church when known

❌ **Don't:**
- Create duplicate records for the same person
- Leave important fields like email blank if known
- Forget to update status when relationships become inactive

---

## Church Management

Churches represent organizations in your CRM system, with comprehensive tracking for institutional relationships.

### Church-Specific Information

#### Core Church Data:
- **Organization Details**: Official name, denomination, location
- **Size Information**: Congregation size, weekly attendance
- **Founded**: Year established
- **Website**: Official church website
- **Contact Information**: Addresses, phone numbers, email

#### Leadership Information:
**Senior Pastor**:
- Name, phone, email
- Separate first/last name fields for better organization

**Missions Pastor**:
- Dedicated fields for missions leadership contact
- Phone and email for missions-specific communication

**Primary Contact**:
- Designated main contact person (can be different from pastor)
- Links to a Person record through ChurchMembership relationship

#### Operational Information:
- **Service Times**: JSON field storing multiple service schedules
- **Facilities**: Information about church buildings and resources
- **Ministries**: List of church programs and ministries
- **Languages**: Primary and secondary languages used

### Adding a New Church

1. **Navigate to Churches**: Click "Churches" in main navigation
2. **Click "Add Church"**: Use the add button
3. **Fill Core Information**:
   - Church Name (required)
   - Location/Address
   - Denomination
   - Website
4. **Add Leadership Details**:
   - Senior Pastor information
   - Missions Pastor (if applicable)
   - Primary Contact designation
5. **Set Operational Details**:
   - Service times
   - Congregation size estimates
   - Ministry information

### Church-People Relationships

The system uses `ChurchMembership` to track relationships between people and churches:

**Relationship Types**:
- **Pastoral Roles**: Senior, Associate, Youth, Worship, Missions, Admin Pastor
- **Leadership Roles**: Elder, Deacon, Board Member, Ministry Leader
- **General Roles**: Member, Regular Attendee, Volunteer

**Membership Management**:
- **One Primary Contact**: Only one person can be designated as primary contact
- **Multiple Roles**: People can have different roles in the same church
- **Status Tracking**: Active, inactive, or former relationships
- **Date Tracking**: Start and end dates for relationships

### Church Pipeline Management

Churches progress through their own pipeline stages:
1. **Promotion**: Initial introduction and awareness
2. **Information**: Detailed information sharing
3. **Invitation**: Formal partnership invitation
4. **Confirmation**: Partnership agreement confirmed
5. **Automation**: Ongoing relationship management
6. **EN42**: Enhanced engagement status (church-specific)

> **💡 Tip**: Use the church-specific "EN42" stage to track churches that have reached the highest level of engagement with your organization.

### Viewing Church Information

**Church List View**:
- **Search**: By name, location, denomination
- **Filter**: By pipeline stage, size, denomination
- **Sort**: By name, creation date, congregation size

**Church Detail View**:
- **Contact Information**: All addresses, phones, emails
- **Leadership Team**: Complete pastoral and leadership details
- **Membership Roster**: All associated people and their roles
- **Communication History**: All interactions with the church
- **Pipeline Progress**: Current stage and movement tracking
- **Tasks**: All church-related tasks and their status

---

## Pipeline Management

The Pipeline system in Mobilize CRM tracks the progression of relationships with both individuals and organizations through defined stages.

### Pipeline Architecture

#### Main Pipelines (Shared Across All Offices)
Mobilize CRM includes two main pipelines that are standardized across your organization:

**People Pipeline**: For tracking individual relationships
**Church Pipeline**: For tracking organizational relationships

These main pipelines cannot be modified and ensure consistency across your organization.

#### Custom Pipelines (Office-Specific)
Individual offices can create custom pipelines that fall under main pipeline stages, allowing for specialized tracking while maintaining overall consistency.

### People Pipeline Stages

#### 1. Promotion
**Purpose**: Initial awareness and interest generation
**Typical Activities**:
- First contact or introduction
- Initial information sharing
- Awareness building
- Interest assessment

**Next Steps**: Move to Information when person shows genuine interest

#### 2. Information
**Purpose**: Detailed information sharing and education
**Typical Activities**:
- Comprehensive presentations
- Q&A sessions
- Resource sharing
- Relationship building

**Next Steps**: Move to Invitation when person demonstrates understanding and continued interest

#### 3. Invitation
**Purpose**: Formal invitation to participate or commit
**Typical Activities**:
- Formal invitation presentation
- Addressing concerns or questions
- Timeline discussions
- Commitment conversations

**Next Steps**: Move to Confirmation when person accepts invitation

#### 4. Confirmation
**Purpose**: Finalizing commitment and next steps
**Typical Activities**:
- Commitment documentation
- Planning next phases
- Setting expectations
- Resource allocation

**Next Steps**: Move to Automation for ongoing relationship management

#### 5. Automation
**Purpose**: Ongoing relationship management and support
**Typical Activities**:
- Regular check-ins
- Automated communications
- Progress monitoring
- Long-term relationship maintenance

### Church Pipeline Stages

Churches follow the same five stages as people, plus an additional stage:

#### 6. EN42 (Church-Specific)
**Purpose**: Enhanced engagement level for churches
**Typical Activities**:
- Advanced partnership activities
- Deep organizational integration
- Strategic collaboration
- Long-term partnership planning

### Managing Pipeline Progression

#### Moving Contacts Through Stages

**Manual Stage Updates**:
1. Open the contact's detail view
2. Locate the "Pipeline Stage" section
3. Select the new stage from the dropdown
4. Add notes about the reason for the move
5. Save changes

**Bulk Stage Updates** (Admin users):
1. Select multiple contacts from list view
2. Choose "Update Pipeline Stage" from bulk actions
3. Select target stage
4. Apply changes to all selected contacts

#### Pipeline History Tracking

The system automatically tracks all pipeline movements:
- **From/To Stages**: Complete movement history
- **Date/Time**: When each movement occurred
- **User**: Who made the change
- **Notes**: Reason for the movement

Access history by viewing the "Pipeline History" section in any contact's detail view.

#### Automated Pipeline Management

**Auto-Move Rules** (Admin Configuration):
- **Time-Based**: Automatically move contacts after specified days
- **Activity-Based**: Move based on completed communications or tasks
- **Reminder System**: Alert users when contacts have been in a stage too long

### Pipeline Reporting and Analytics

#### Stage Distribution Reports
View how your contacts are distributed across pipeline stages:
- **Visual Charts**: Pie charts and bar graphs
- **Percentage Breakdowns**: Stage distribution percentages
- **Trend Analysis**: Movement patterns over time

#### Pipeline Performance Metrics
- **Conversion Rates**: Percentage moving between stages
- **Average Time**: How long contacts spend in each stage
- **Bottleneck Analysis**: Stages where contacts get stuck
- **Success Tracking**: Completion rates through the pipeline

### Best Practices for Pipeline Management

✅ **Do:**
- **Move Contacts Regularly**: Keep pipeline status current
- **Add Movement Notes**: Explain why contacts are moving stages
- **Review Stagnant Contacts**: Address contacts stuck in stages too long
- **Use Automation**: Set up auto-moves where appropriate
- **Track Conversations**: Update stages after meaningful interactions

❌ **Don't:**
- **Skip Stages**: Maintain logical progression through pipeline
- **Ignore History**: Review past movements before making changes
- **Mass Move Without Reason**: Bulk changes should have clear justification
- **Set Unrealistic Timelines**: Allow appropriate time for each stage

> **💡 Tip**: Use the dashboard's pipeline distribution widgets to monitor your overall pipeline health and identify stages needing attention.

---

## Task Management

Mobilize CRM includes a comprehensive task management system for tracking follow-ups, reminders, and action items related to your contacts and churches.

### Understanding Tasks

#### Task Types and Categories
Tasks in Mobilize CRM can be:
- **Contact-Related**: Associated with specific people or churches
- **General**: Not tied to specific contacts
- **Recurring**: Automatically generated based on schedules
- **Project-Based**: Part of larger initiatives

#### Task Priority Levels
- **High**: Urgent tasks requiring immediate attention
- **Medium**: Important tasks with standard priority
- **Low**: Tasks that can be completed when time allows

#### Task Status Options
- **Pending**: Not yet started
- **In Progress**: Currently being worked on
- **Completed**: Finished tasks

### Creating Tasks

#### Basic Task Creation
1. **Access Task Creation**:
   - From Dashboard: Click "Create Task" quick action
   - From Navigation: Go to Tasks → Add New Task
   - From Contact View: Use "Add Task" button in contact details

2. **Fill Required Information**:
   - **Title**: Clear, actionable task description
   - **Description**: Detailed task information
   - **Due Date**: When the task should be completed
   - **Priority**: High, Medium, or Low
   - **Assignee**: User responsible for completion

3. **Associate with Contacts** (Optional):
   - Link to specific Person
   - Link to specific Church
   - Link to general Contact record

#### Advanced Task Options

**Due Time Settings**:
- **Due Date**: Calendar date
- **Due Time**: Specific time of day
- **Time Details**: Additional timing context

**Reminder Configuration**:
- **Reminder Time**: When to send notifications
- **Reminder Options**: Email, in-system, or none
- **Notification Preferences**: Customize reminder delivery

**Google Calendar Integration**:
- **Sync to Calendar**: Automatically create calendar events
- **Calendar Event Details**: Meeting links, locations
- **Two-Way Sync**: Updates flow between systems

### Recurring Tasks

Mobilize CRM supports sophisticated recurring task patterns for ongoing activities.

#### Creating Recurring Tasks

1. **Enable Recurring Pattern**: Check "Make this a recurring task"
2. **Set Frequency Options**:
   - **Daily**: Every N days
   - **Weekly**: Specific days of the week, every N weeks
   - **Monthly**: Specific day of month, every N months
   - **Yearly**: Annual recurring tasks

3. **Configure Pattern Details**:
   ```json
   Example Weekly Pattern:
   {
     "frequency": "weekly",
     "interval": 1,
     "weekdays": [0, 2, 4],  // Monday, Wednesday, Friday
     "end_date": "2025-12-31"
   }
   ```

#### Recurring Task Management

**Template System**:
- **Master Template**: The original recurring task definition
- **Generated Instances**: Individual task occurrences
- **Next Occurrence**: Automatically calculated next due date

**Automatic Generation**:
- Tasks are automatically created based on the recurring pattern
- Generation happens via scheduled background processes
- Tasks are created up to 7 days in advance

### Task Assignment and Collaboration

#### Assignment Options
- **Self-Assignment**: Assign tasks to yourself
- **Team Assignment**: Assign to other users in your office
- **Cross-Office Assignment**: Super Admins can assign across offices

#### Task Notifications
- **Assignment Notifications**: Alert when tasks are assigned to you
- **Reminder Notifications**: Due date and overdue reminders
- **Completion Notifications**: Alerts when assigned tasks are completed

#### Collaborative Features
- **Task Comments**: Add updates and progress notes
- **Status Updates**: Track progress through completion
- **Handoff Management**: Transfer tasks between team members

### Managing Your Tasks

#### Task List Views

**My Tasks Dashboard**:
- **Overdue Tasks**: Past-due items requiring immediate attention
- **Due Today**: Tasks due on current date
- **Due This Week**: Upcoming tasks in next 7 days
- **All Active Tasks**: Complete list of pending and in-progress tasks

**Filtering and Searching**:
- **Filter by Status**: Pending, In Progress, Completed
- **Filter by Priority**: High, Medium, Low
- **Filter by Assignment**: Tasks assigned to you vs. created by you
- **Filter by Contact**: Tasks related to specific people or churches
- **Date Range Filters**: Due date ranges
- **Text Search**: Search task titles and descriptions

#### Task Detail Management

**Updating Task Progress**:
1. Open task detail view
2. Update status (Pending → In Progress → Completed)
3. Add progress notes or comments
4. Update due date if needed
5. Save changes

**Task Completion**:
1. Change status to "Completed"
2. Add completion notes
3. Automatic timestamp recording
4. Notification to task creator (if different from assignee)

### Google Calendar Integration

#### Automatic Calendar Sync
When enabled, tasks automatically create Google Calendar events:
- **Event Creation**: New tasks become calendar events
- **Two-Way Updates**: Changes sync between systems
- **Meeting Integration**: Add Google Meet links for meeting tasks

#### Calendar Sync Settings
Configure calendar integration in your user settings:
- **Enable/Disable Sync**: Turn calendar integration on/off
- **Calendar Selection**: Choose which Google Calendar to use
- **Event Details**: Customize what information appears in calendar events

### Task Reporting and Analytics

#### Personal Task Reports
- **Completion Rates**: Percentage of tasks completed on time
- **Overdue Analysis**: Patterns in overdue tasks
- **Productivity Metrics**: Tasks completed per day/week/month
- **Category Breakdown**: Task distribution by type or priority

#### Team Task Reports (Managers)
- **Team Performance**: Completion rates across team members
- **Workload Distribution**: Task assignment balance
- **Bottleneck Analysis**: Where tasks get delayed
- **Recurring Task Efficiency**: Pattern effectiveness analysis

### Best Practices for Task Management

✅ **Do:**
- **Use Descriptive Titles**: Make tasks clear and actionable
- **Set Realistic Due Dates**: Allow appropriate time for completion
- **Update Progress Regularly**: Keep status current
- **Use Contact Associations**: Link tasks to relevant people/churches
- **Review Recurring Patterns**: Adjust frequencies based on effectiveness
- **Set Appropriate Priorities**: Use priority levels meaningfully

❌ **Don't:**
- **Create Vague Tasks**: Avoid unclear or non-actionable descriptions
- **Ignore Due Dates**: Don't let tasks become chronically overdue
- **Over-assign**: Avoid overwhelming team members with too many high-priority tasks
- **Forget to Complete**: Mark tasks complete when finished
- **Ignore Recurring Tasks**: Monitor and adjust recurring patterns

> **💡 Tip**: Use the dashboard's task widgets to monitor your task health and stay on top of important deadlines.

---

## Email Integration (Gmail)

Mobilize CRM provides deep integration with Gmail, allowing you to manage all your contact communications within the CRM while maintaining your normal email workflow.

### Gmail Integration Overview

#### What Gets Synced
- **Sent Emails**: Messages you send to people in your CRM
- **Received Emails**: Messages you receive from CRM contacts
- **Email Metadata**: Subject lines, dates, thread information
- **Contact Matching**: Automatic linking to Person/Church records
- **Thread Tracking**: Conversation history maintenance

#### Integration Permissions
The system requires specific Google OAuth permissions:
- **Gmail Compose**: Send emails through the CRM
- **Gmail Send**: Send emails on your behalf
- **Gmail Readonly**: Access your email messages
- **Google Contacts**: Sync with Google Contacts when enabled

### Setting Up Gmail Integration

#### Initial Authorization
1. **Navigate to Settings**: Click your profile → Settings
2. **Gmail Integration Section**: Find the Gmail connection status
3. **Connect Gmail**: Click "Connect Gmail Account"
4. **Authorize Permissions**: Grant necessary OAuth permissions
5. **Confirmation**: Verify connection status shows "Connected"

#### Sync Settings Configuration
Configure how emails are synchronized:

**Sync Preferences**:
- **Contacts Only**: Sync only emails from/to people in your CRM
- **All Emails**: Sync all emails (use cautiously)
- **Selective Sync**: Choose specific email addresses or domains

**Sync Frequency**:
- **Real-time**: Immediate sync (recommended)
- **Hourly**: Sync every hour
- **Daily**: Sync once per day
- **Manual**: Sync only when requested

**Historical Sync**:
- **Days Back**: How many days of historical emails to import
- **Initial Sync**: Full historical import vs. going-forward only

### Using Gmail Integration

#### Viewing Email History

**From Contact Records**:
1. Open any Person or Church detail view
2. Navigate to "Communications" tab
3. View complete email history with this contact
4. See both sent and received messages

**Email Details Include**:
- **Subject Line**: Email subject
- **Send/Receive Date**: Timestamp
- **Direction**: Inbound or outbound
- **Content Preview**: First few lines of email content
- **Thread Information**: Related messages in conversation

#### Sending Emails Through CRM

**Compose New Email**:
1. **From Contact Record**: Click "Send Email" button
2. **From Communications**: Use "Compose" button
3. **Email Form Fields**:
   - **To**: Pre-populated with contact email
   - **CC/BCC**: Additional recipients
   - **Subject**: Email subject line
   - **Body**: Message content with rich text editor
   - **Template**: Use saved email templates
   - **Signature**: Automatically append email signature

**Email Templates**:
- **Pre-defined Messages**: Common email types
- **Personalization**: Merge contact information
- **Category Organization**: Templates by purpose
- **Rich Text Support**: Formatting, images, links

#### Email Tracking and Analytics

**Individual Email Tracking**:
- **Delivery Status**: Sent, delivered, failed
- **Open Tracking**: When recipients open emails (if supported)
- **Response Tracking**: Automatic thread matching for replies

**Communication History**:
- **Complete Thread View**: Entire email conversations
- **Contact Context**: All emails with specific contacts
- **Timeline Integration**: Emails in overall communication timeline

### Advanced Gmail Features

#### Email Templates

**Creating Templates**:
1. **Navigate to Communications** → Email Templates
2. **Click "Add Template"**
3. **Fill Template Details**:
   - **Name**: Template identifier
   - **Subject**: Email subject (can include merge fields)
   - **Body**: Email content with merge fields
   - **Category**: Organizational grouping
   - **HTML**: Enable rich text formatting

**Merge Fields** (Contact Personalization):
- `{{first_name}}`: Contact's first name
- `{{last_name}}`: Contact's last name
- `{{church_name}}`: Associated church name
- `{{email}}`: Contact's email address

**Template Usage**:
- Select template when composing emails
- Automatic merge field replacement
- Customization after template selection

#### Email Signatures

**Signature Management**:
1. **Access Settings** → Email Signatures
2. **Create New Signature**:
   - **Name**: Signature identifier
   - **Content**: HTML signature content
   - **Logo**: Upload or link to logo image
   - **Default**: Set as default signature

**Signature Features**:
- **HTML Support**: Rich formatting, images, links
- **Logo Integration**: Company/organization branding
- **Multiple Signatures**: Different signatures for different purposes
- **Automatic Append**: Added to all outgoing emails

#### Bulk Email Capabilities

**Mass Communications**:
1. **Select Recipients**: Filter contacts for bulk email
2. **Choose Template**: Use appropriate email template
3. **Personalization**: Automatic merge field replacement
4. **Send Configuration**:
   - **Immediate Send**: Send all emails now
   - **Scheduled Send**: Send at specific time
   - **Batch Processing**: Send in groups to avoid spam triggers

**Bulk Email Best Practices**:
- **Respect Recipients**: Only email people who expect communication
- **Personalization**: Use merge fields for personal touch
- **Unsubscribe Options**: Include opt-out mechanisms
- **Compliance**: Follow email marketing regulations

### Gmail Sync Settings

#### Individual User Settings

**Sync Preferences** (User Settings → Gmail Integration):
- **Enable Sync**: Turn synchronization on/off
- **Sync Mode**: Contacts only vs. all emails
- **Historical Range**: How far back to sync
- **Frequency**: How often to check for new emails

#### Advanced Sync Options

**Contact Matching Rules**:
- **Email Address Matching**: Primary matching method
- **Name Fuzzy Matching**: Similar name matching
- **Domain Filtering**: Organization-specific email domains
- **Manual Associations**: Override automatic matching

**Sync Performance**:
- **Batch Size**: Number of emails processed at once
- **Rate Limiting**: Avoid hitting Google API limits
- **Error Handling**: Automatic retry for failed syncs
- **Progress Tracking**: Monitor sync status and progress

### Troubleshooting Gmail Integration

#### Common Issues

**Connection Problems**:
- **Token Expiration**: Re-authorize Google permissions
- **Permission Changes**: Verify all required scopes granted
- **Account Issues**: Check Google account status

**Sync Issues**:
- **Missing Emails**: Check sync date ranges and contact matching
- **Duplicate Messages**: Review sync settings and filters
- **Performance Issues**: Adjust batch sizes and frequency

**Email Sending Problems**:
- **Authentication Errors**: Re-connect Gmail account
- **Rate Limiting**: Reduce sending frequency
- **Spam Detection**: Review email content and sending patterns

#### Resolution Steps
1. **Check Connection Status**: Verify Gmail integration is active
2. **Review Error Messages**: Look for specific error details in settings
3. **Re-authorize**: Disconnect and reconnect Gmail account
4. **Contact Support**: Provide specific error messages and context

### Best Practices for Gmail Integration

✅ **Do:**
- **Regular Sync**: Keep email integration active for best results
- **Clean Contact Data**: Maintain accurate email addresses
- **Use Templates**: Leverage email templates for efficiency
- **Monitor Sync**: Regularly check sync status and resolve issues
- **Personalize Communications**: Use merge fields for personal touch

❌ **Don't:**
- **Sync Everything**: Be selective about which emails to sync
- **Ignore Permissions**: Don't skip required OAuth permissions
- **Mass Email Without Permission**: Respect recipients' communication preferences
- **Forget Signatures**: Always include professional email signatures
- **Ignore Errors**: Address sync errors promptly to maintain data accuracy

> **💡 Tip**: Use the Gmail integration's "Contacts Only" sync mode to keep your CRM focused on relevant communications while avoiding information overload.

---

## Calendar Integration

Mobilize CRM integrates with Google Calendar to help you manage appointments, meetings, and task-related events directly within your CRM workflow.

### Calendar Integration Overview

#### What Gets Synced
- **Task-Related Events**: Tasks with due times become calendar events
- **Meeting Communications**: Meeting-type communications sync to calendar
- **Appointment Scheduling**: CRM appointments appear on your calendar
- **Two-Way Synchronization**: Changes flow between CRM and Google Calendar

#### Integration Benefits
- **Unified Scheduling**: See CRM activities alongside personal events
- **Automatic Reminders**: Google Calendar notifications for CRM activities
- **Meeting Links**: Google Meet integration for virtual meetings
- **Mobile Access**: Calendar events available on all devices

### Setting Up Calendar Integration

#### Initial Configuration
1. **Google OAuth**: Calendar access is included in Gmail integration setup
2. **Calendar Selection**: Choose which Google Calendar to use for CRM events
3. **Sync Preferences**: Configure what types of events to sync
4. **Notification Settings**: Set up calendar notification preferences

#### Calendar Sync Settings

**Event Types to Sync**:
- ✅ **Tasks with Due Times**: Tasks become calendar events
- ✅ **Meeting Communications**: Meeting records create calendar events
- ✅ **Appointments**: Scheduled appointments with contacts
- ⚪ **All Communications**: All communication records (optional)

**Event Details Configuration**:
- **Event Title Format**: How CRM events appear in calendar
- **Description Content**: What information to include
- **Duration Settings**: Default meeting lengths
- **Privacy Settings**: Public vs. private events

### Using Calendar Features

#### Task-Calendar Integration

**Automatic Event Creation**:
When you create a task with a due time, the system automatically:
1. Creates a Google Calendar event
2. Sets the event time to match the task due time
3. Includes task details in the event description
4. Links the calendar event back to the CRM task

**Event Details Include**:
- **Title**: Task title with "Task: " prefix
- **Description**: Task description and contact information
- **Location**: Contact address (if applicable)
- **Attendees**: Task assignee and related contacts

#### Meeting Management

**Scheduling Meetings with Contacts**:
1. **From Contact Record**: Click "Schedule Meeting"
2. **Meeting Details**:
   - **Date/Time**: When the meeting will occur
   - **Duration**: How long the meeting will last
   - **Type**: In-person, phone call, video call
   - **Location**: Meeting location or video link
3. **Calendar Integration**: Meeting automatically appears on calendar
4. **Communication Record**: Meeting details saved in CRM

**Google Meet Integration**:
- **Automatic Links**: Video meetings get Google Meet links
- **Join Information**: Meet details included in calendar events
- **Contact Invitations**: Optionally invite contacts to calendar events

#### Appointment Scheduling

**Creating Appointments**:
- **Direct Scheduling**: Create appointments from contact records
- **Calendar Blocking**: Block time for CRM activities
- **Follow-up Reminders**: Automatic reminder tasks for post-meeting actions

### Calendar Event Management

#### Viewing CRM Events

**In Google Calendar**:
- CRM events appear alongside personal events
- Special formatting identifies CRM-related events
- Click events to view CRM details

**In Mobilize CRM**:
- **Calendar View**: Integrated calendar showing CRM events
- **Task Calendar**: Filter to show only task-related events
- **Contact Calendar**: View all events related to specific contacts

#### Modifying Calendar Events

**Two-Way Sync**:
- **Time Changes**: Update event times in either system
- **Status Updates**: Mark tasks complete from calendar
- **Detail Updates**: Modify descriptions and details

**Sync Limitations**:
- **Deletion**: Deleting calendar events doesn't delete CRM tasks
- **Attendee Changes**: Contact invitations managed through CRM
- **Recurring Events**: Complex recurring patterns may not sync perfectly

### Calendar Reporting and Analytics

#### Meeting Analytics
- **Meeting Frequency**: How often you meet with contacts
- **Meeting Types**: Distribution of meeting formats
- **Follow-up Tracking**: Post-meeting task completion rates
- **Time Investment**: Hours spent in contact meetings

#### Schedule Analysis
- **CRM Time Allocation**: Time spent on CRM activities
- **Peak Activity Times**: When most meetings occur
- **Contact Engagement**: Meeting frequency by contact type
- **Productivity Metrics**: Meeting outcomes and effectiveness

### Advanced Calendar Features

#### Bulk Calendar Operations

**Mass Meeting Scheduling**:
- **Multi-Contact Meetings**: Schedule meetings with multiple contacts
- **Recurring Meeting Series**: Set up regular check-ins
- **Template-Based Scheduling**: Use meeting templates for consistency

**Calendar Maintenance**:
- **Cleanup Tools**: Remove old or canceled events
- **Sync Refresh**: Force full calendar synchronization
- **Conflict Resolution**: Handle scheduling conflicts

#### Integration with Other Features

**Task Integration**:
- **Pre-Meeting Tasks**: Automatically create preparation tasks
- **Post-Meeting Follow-ups**: Generate follow-up tasks after meetings
- **Meeting Outcomes**: Link meeting results to pipeline progression

**Communication Integration**:
- **Meeting Invitations**: Send meeting invites through email system
- **Confirmation Emails**: Automatic meeting confirmations
- **Follow-up Communications**: Templated post-meeting emails

### Calendar Settings and Preferences

#### User Calendar Settings

**Sync Preferences**:
- **Calendar Selection**: Choose target Google Calendar
- **Event Types**: Select which events to sync
- **Sync Direction**: One-way vs. two-way synchronization
- **Historical Sync**: How far back to sync existing events

**Notification Settings**:
- **Calendar Reminders**: Google Calendar notification timing
- **CRM Notifications**: In-app notifications for calendar events
- **Email Reminders**: Email notifications for upcoming meetings

#### System-Wide Calendar Settings (Admin)

**Default Settings**:
- **Meeting Duration**: Standard meeting lengths
- **Buffer Times**: Automatic buffer between meetings
- **Working Hours**: Business hour constraints
- **Holiday Calendar**: Organization holiday integration

**Integration Rules**:
- **Auto-Sync Rules**: What events automatically sync
- **Privacy Controls**: What information appears in calendar events
- **Access Permissions**: Who can view calendar integration status

### Troubleshooting Calendar Integration

#### Common Issues

**Sync Problems**:
- **Events Not Appearing**: Check calendar selection and permissions
- **Duplicate Events**: Review sync settings and filters
- **Time Zone Issues**: Verify time zone consistency

**Meeting Scheduling Issues**:
- **Conflicts**: Calendar shows conflicts with existing events
- **Invitation Problems**: Contacts not receiving calendar invites
- **Google Meet Links**: Video links not generating properly

#### Resolution Steps
1. **Verify Permissions**: Ensure Google Calendar access is granted
2. **Check Settings**: Review calendar sync preferences
3. **Force Sync**: Manually trigger calendar synchronization
4. **Clear Cache**: Reset calendar integration cache
5. **Re-authorize**: Disconnect and reconnect Google integration

### Best Practices for Calendar Integration

✅ **Do:**
- **Keep Calendars Synced**: Regular synchronization for accuracy
- **Use Consistent Time Zones**: Avoid scheduling conflicts
- **Include Context**: Add meaningful descriptions to calendar events
- **Set Reminders**: Use calendar notifications for important meetings
- **Track Follow-ups**: Create post-meeting tasks for accountability

❌ **Don't:**
- **Over-Sync**: Don't sync every CRM activity to calendar
- **Ignore Conflicts**: Address scheduling conflicts promptly
- **Forget Privacy**: Be mindful of what contact information appears in calendar
- **Skip Follow-ups**: Don't let meetings end without next steps
- **Ignore Notifications**: Pay attention to calendar reminders

> **💡 Tip**: Use calendar integration to create a seamless workflow between your CRM activities and personal schedule, ensuring you never miss important contact meetings or task deadlines.

---

## Reports and Analytics

Mobilize CRM provides comprehensive reporting and analytics capabilities to help you understand your contact relationships, track progress, and make data-driven decisions.

### Report Categories

#### 1. Contact Reports
- **People Report**: Complete list of individual contacts
- **Church Report**: Organizational contact details
- **Contact Summary**: Overview of all contacts with key metrics
- **Pipeline Distribution**: Contact distribution across pipeline stages
- **Contact Activity**: Recent additions and updates

#### 2. Communication Reports
- **Communication History**: All emails, calls, and meetings
- **Email Analytics**: Send rates, open rates, response rates
- **Contact Frequency**: Communication patterns by contact
- **Template Usage**: Email template effectiveness
- **Response Analysis**: Response rates and timing

#### 3. Task Reports
- **Task Completion**: Completed vs. pending tasks
- **Overdue Analysis**: Tasks past their due dates
- **Assignment Distribution**: Task distribution by team member
- **Productivity Metrics**: Tasks completed per time period
- **Recurring Task Performance**: Effectiveness of recurring patterns

#### 4. Pipeline Reports
- **Stage Analysis**: Time spent in each pipeline stage
- **Conversion Rates**: Movement rates between stages
- **Pipeline Health**: Overall pipeline performance
- **Bottleneck Analysis**: Stages where contacts get stuck
- **Trend Analysis**: Pipeline changes over time

### Generating Reports

#### Accessing Reports
1. **Navigate to Reports**: Click "Reports" in main navigation
2. **Select Report Type**: Choose from available report categories
3. **Configure Parameters**: Set date ranges, filters, and options
4. **Generate Report**: Create the report with current data
5. **Export or View**: Download or view online

#### Report Parameters

**Date Ranges**:
- **Last 7 Days**: Recent activity focus
- **Last 30 Days**: Monthly analysis
- **Last 90 Days**: Quarterly review
- **Year to Date**: Annual progress tracking
- **Custom Range**: Specific date range selection

**Data Filters**:
- **View Mode**: Personal data vs. office data vs. all data (based on permissions)
- **Contact Types**: People only, churches only, or both
- **Pipeline Stages**: Specific stages or all stages
- **Task Status**: Pending, completed, or overdue tasks
- **Communication Types**: Emails, calls, meetings, or all

#### Export Formats

**CSV (Comma-Separated Values)**:
- **Use Case**: Data analysis in Excel or Google Sheets
- **Advantages**: Universal format, easy to manipulate
- **Best For**: Contact lists, task reports, communication logs

**PDF (Portable Document Format)**:
- **Use Case**: Formal reports, presentations, documentation
- **Advantages**: Professional formatting, print-ready
- **Best For**: Executive summaries, formal analysis

**Excel (XLSX)**:
- **Use Case**: Advanced data analysis and manipulation
- **Advantages**: Formulas, charts, advanced formatting
- **Best For**: Complex analysis, data visualization

### Data Visualization

#### Dashboard Analytics

**Pipeline Charts**:
- **Distribution Pie Charts**: Visual stage distribution
- **Progress Bar Charts**: Movement through pipeline
- **Trend Line Graphs**: Pipeline changes over time

**Activity Timeline**:
- **7-Day Activity Chart**: Daily activity visualization
- **Monthly Trends**: Longer-term pattern analysis
- **Comparison Charts**: Current vs. previous periods

#### Report Visualizations

**Contact Analytics**:
- **Growth Charts**: Contact acquisition over time
- **Geographic Distribution**: Contact location mapping
- **Source Analysis**: Where contacts originate

**Communication Analysis**:
- **Volume Charts**: Communication frequency trends
- **Response Rate Graphs**: Email effectiveness metrics
- **Channel Distribution**: Communication method preferences

### Advanced Analytics

#### Performance Metrics

**Contact Relationship Health**:
- **Engagement Scores**: Contact interaction frequency
- **Response Rates**: How often contacts respond to communications
- **Pipeline Velocity**: Speed of movement through stages
- **Relationship Strength**: Multiple interaction indicators

**Team Performance** (Managers):
- **Individual Productivity**: Performance by team member
- **Task Completion Rates**: Efficiency metrics
- **Communication Volume**: Activity levels
- **Pipeline Management**: Stage movement effectiveness

#### Trend Analysis

**Historical Comparisons**:
- **Period-over-Period**: Month-to-month, year-over-year comparisons
- **Growth Trends**: Contact acquisition and engagement trends
- **Seasonal Patterns**: Activity patterns by time of year
- **Success Indicators**: Leading indicators of positive outcomes

#### Predictive Analytics

**Contact Scoring** (Advanced Feature):
- **Engagement Prediction**: Likelihood of continued engagement
- **Conversion Probability**: Chance of pipeline progression
- **Risk Assessment**: Contacts at risk of disengagement

### Custom Reporting

#### Report Builder (Admin Feature)

**Custom Query Builder**:
- **Field Selection**: Choose specific data fields
- **Filter Criteria**: Multiple filter combinations
- **Grouping Options**: Organize data by categories
- **Sorting Rules**: Custom data ordering

**Saved Reports**:
- **Report Templates**: Save frequently used report configurations
- **Scheduled Reports**: Automatic report generation and delivery
- **Shared Reports**: Team-wide report access

#### API-Based Reporting (Advanced)

**Data Export APIs**:
- **Real-time Data Access**: Live data querying
- **Integration Capabilities**: Connect with external tools
- **Custom Applications**: Build specialized reporting tools

### Report Permissions and Access

#### Role-Based Report Access

**Super Admin**:
- **All Data**: Complete organizational reporting
- **System Reports**: User activity and system health
- **Cross-Office Analysis**: Multi-office comparisons

**Office Admin**:
- **Office Data**: Complete office reporting
- **Team Performance**: Staff productivity and activity
- **Office Comparisons**: Historical office performance

**Standard User**:
- **Personal Data**: Individual contact and task reports
- **Team Data**: Shared office contacts and activities
- **Limited Analytics**: Basic performance metrics

**Limited User**:
- **View-Only Reports**: Read-access to generated reports
- **Personal Metrics**: Individual productivity only

#### Data Privacy and Security

**Access Controls**:
- **Role-Based Filters**: Automatic data filtering by permissions
- **Contact Visibility**: Respect contact access restrictions
- **Audit Logging**: Track report generation and access

**Data Protection**:
- **Export Logging**: Record all data exports
- **Secure Transmission**: Encrypted data transfers
- **Retention Policies**: Automatic report cleanup

### Using Reports for Decision Making

#### Strategic Planning

**Growth Analysis**:
- **Contact Acquisition**: Track recruitment effectiveness
- **Pipeline Health**: Identify growth opportunities
- **Resource Allocation**: Optimize team assignments

**Performance Improvement**:
- **Bottleneck Identification**: Find process inefficiencies
- **Success Pattern Analysis**: Replicate effective strategies
- **Training Needs**: Identify skill gaps and training opportunities

#### Operational Management

**Daily Operations**:
- **Task Management**: Monitor task completion and overdue items
- **Communication Tracking**: Ensure consistent contact engagement
- **Activity Planning**: Plan daily and weekly activities

**Team Management**:
- **Workload Balancing**: Distribute tasks and contacts effectively
- **Performance Recognition**: Identify high performers
- **Support Needs**: Provide assistance where needed

### Best Practices for Reporting

✅ **Do:**
- **Regular Reporting**: Generate reports consistently for trend analysis
- **Multiple Formats**: Use appropriate formats for different audiences
- **Data Validation**: Verify report accuracy before sharing
- **Action-Oriented Analysis**: Use reports to drive decisions and actions
- **Historical Tracking**: Maintain report history for comparison

❌ **Don't:**
- **Over-Report**: Don't generate reports that won't be used
- **Ignore Context**: Consider external factors affecting data
- **Share Inappropriate Data**: Respect privacy and permission boundaries
- **Analysis Paralysis**: Don't let reporting replace action
- **Stale Data**: Don't use outdated reports for current decisions

> **💡 Tip**: Set up a regular reporting schedule (weekly, monthly, quarterly) to track progress consistently and identify trends early.

---

## User Settings and Preferences

Mobilize CRM provides extensive customization options to tailor the system to your personal workflow and preferences.

### Accessing User Settings

#### Navigation to Settings
1. **Click Profile Menu**: Your name/avatar in the top navigation
2. **Select "Settings"**: Opens the settings page
3. **Navigate Sections**: Use tabs or sections to access different preference categories

### Profile Management

#### Basic Profile Information
- **First/Last Name**: Your display name throughout the system
- **Email Address**: Primary contact email (linked to Google OAuth)
- **Phone Number**: Optional contact information
- **Profile Picture**: Upload custom avatar or use Google profile photo

#### Profile Integration
- **Person Record Link**: Your user account is automatically linked to a Person record in the CRM
- **Contact Information Sync**: Profile changes update your Person record
- **Visibility Settings**: Control how your information appears to other users

### Email and Communication Settings

#### Gmail Integration Settings

**Connection Management**:
- **Connection Status**: View current Gmail integration status
- **Re-authorization**: Reconnect Gmail account if needed
- **Permission Review**: See what permissions are granted
- **Disconnect**: Remove Gmail integration

**Sync Preferences**:
```
Sync Options:
□ Sync only emails from CRM contacts
□ Sync all emails (use with caution)
□ Enable automatic background sync
□ Create tasks for follow-up emails
```

**Historical Email Import**:
- **Days to Sync Back**: 7, 30, 90 days, or custom range
- **Initial Sync**: Full import vs. going-forward only
- **Contact Matching**: Automatic vs. manual contact linking

#### Email Composition Settings

**Default Templates**:
- **Signature Selection**: Choose default email signature
- **Template Preferences**: Favorite email templates
- **Auto-Complete**: Enable contact email suggestions

**Sending Preferences**:
- **Send Immediately**: Send emails right away vs. review before sending
- **Copy to Self**: Automatically BCC yourself on sent emails
- **Tracking**: Enable email open tracking (when available)

### Calendar Integration Settings

#### Google Calendar Sync

**Calendar Selection**:
- **Target Calendar**: Which Google Calendar to use for CRM events
- **Calendar Name**: Custom naming for CRM events
- **Color Coding**: How CRM events appear in calendar

**Sync Rules**:
```
Event Types to Sync:
☑ Tasks with due times
☑ Scheduled meetings
☑ Appointments with contacts
☐ All communication records (optional)
```

**Event Formatting**:
- **Title Format**: How event titles appear
- **Description Content**: What details to include
- **Duration Defaults**: Standard meeting lengths

### Notification Preferences

#### System Notifications

**Task Notifications**:
- **New Assignment**: When tasks are assigned to you
- **Due Date Reminders**: How far in advance to remind
- **Overdue Alerts**: Notification for overdue tasks
- **Completion Updates**: When others complete tasks you created

**Communication Notifications**:
- **New Messages**: Incoming emails from CRM contacts
- **Email Delivery**: Send confirmation for outgoing emails
- **Response Alerts**: When contacts reply to your emails

#### Notification Delivery Methods

**In-App Notifications**:
- **Real-time Alerts**: Immediate notifications within CRM
- **Notification Center**: Central location for all alerts
- **Mark as Read**: Notification management

**Email Notifications**:
- **Daily Digest**: Summary of daily activity
- **Weekly Summary**: Weekly productivity and activity report
- **Immediate Alerts**: Real-time email notifications

**Browser Notifications** (if enabled):
- **Desktop Alerts**: Pop-up notifications on your computer
- **Permission Required**: Browser must allow notifications

### Dashboard Customization

#### Widget Configuration

**Available Widgets**:
- **Contact Metrics**: People and church counts
- **Task Summary**: Pending and overdue tasks
- **Communication Activity**: Recent emails and calls
- **Pipeline Distribution**: Contact stage breakdown
- **Activity Timeline**: 7-day activity chart
- **Upcoming Events**: Calendar integration

**Widget Management**:
1. **Enable/Disable**: Turn widgets on/off
2. **Rearrange Layout**: Drag and drop positioning
3. **Resize Widgets**: Adjust column spans (1-4 columns)
4. **Reset Layout**: Return to default configuration

#### Dashboard View Modes (Admin Users)

**View Mode Options**:
- **Default View**: Standard role-based data visibility
- **My Only**: Only data you created or are assigned
- **All Data**: Complete organizational view (Super Admin only)

**Office Selection** (Super Admin):
- **Office Filter**: View specific office data
- **Cross-Office Comparison**: Multi-office analytics

### Contact Management Preferences

#### Contact Display Options

**List View Preferences**:
- **Default Sorting**: How contacts are ordered by default
- **Columns Displayed**: Which fields appear in list views
- **Page Size**: Number of contacts per page (25, 50, 100)
- **Filter Defaults**: Pre-set filters for contact lists

**Detail View Options**:
- **Section Ordering**: Arrange contact detail sections
- **Default Tabs**: Which tab opens first in contact details
- **Field Visibility**: Show/hide specific fields

#### Contact Sync Settings

**Google Contacts Integration**:
- **Sync Preference**: Disabled, CRM only, all contacts, selective
- **Auto-Sync**: Enable automatic contact synchronization
- **Sync Frequency**: How often to sync (hourly, daily, weekly)
- **Conflict Resolution**: How to handle duplicate contacts

### Task Management Preferences

#### Task Display and Organization

**Task List Preferences**:
- **Default View**: My tasks, assigned tasks, or all tasks
- **Sorting Options**: By due date, priority, or creation date
- **Grouping**: Group by status, priority, or assignee
- **Filter Defaults**: Pre-applied filters for task lists

**Task Creation Defaults**:
- **Default Priority**: Medium priority for new tasks
- **Default Assignment**: Self-assign or leave unassigned
- **Reminder Settings**: Default reminder timing
- **Calendar Sync**: Automatically sync tasks to calendar

#### Recurring Task Preferences

**Default Patterns**:
- **Common Frequencies**: Quick-select recurring patterns
- **Working Days**: Define your work schedule for recurring tasks
- **Holiday Handling**: How recurring tasks handle holidays

### Privacy and Security Settings

#### Data Access and Sharing

**Contact Visibility**:
- **Default Access**: Who can see contacts you create
- **Sharing Preferences**: Allow others to assign you tasks
- **Office Boundaries**: Cross-office contact visibility

**Activity Tracking**:
- **Login History**: View your recent login activity
- **Data Access Log**: See who has accessed your data
- **Export History**: Track data exports you've performed

#### Security Preferences

**Authentication**:
- **Password Changes**: Update account password (if applicable)
- **Two-Factor Authentication**: Enable additional security
- **Session Management**: Active session monitoring

**Data Protection**:
- **Export Permissions**: Control who can export your data
- **Audit Trail**: Enable detailed activity logging
- **Privacy Mode**: Limit visibility in system logs

### Advanced Settings

#### System Preferences

**Performance Options**:
- **Cache Settings**: Enable/disable data caching for speed
- **Auto-Save**: Automatically save form changes
- **Offline Mode**: Enable offline data access (where available)

**Integration Management**:
- **API Access**: Personal API key for external integrations
- **Webhook Configuration**: Custom webhook endpoints
- **Third-Party Connections**: Manage external service connections

#### Backup and Export

**Data Backup**:
- **Personal Data Export**: Download your complete data
- **Regular Backups**: Schedule automatic data exports
- **Export Format**: Choose backup file formats

### Settings Management

#### Saving and Applying Changes

**Change Management**:
- **Save Settings**: Apply changes immediately
- **Cancel Changes**: Revert unsaved modifications
- **Reset to Defaults**: Restore original settings

**Settings Validation**:
- **Error Checking**: Validate settings before saving
- **Conflict Resolution**: Handle conflicting preferences
- **Change Confirmation**: Confirm significant setting changes

#### Settings Import/Export (Advanced)

**Profile Portability**:
- **Export Settings**: Save preferences to file
- **Import Settings**: Load preferences from file
- **Team Templates**: Share setting configurations with team

### Best Practices for User Settings

✅ **Do:**
- **Regular Review**: Periodically review and update preferences
- **Test Changes**: Try new settings in non-critical situations
- **Backup Settings**: Export settings before major changes
- **Optimize Workflow**: Adjust settings to match your work patterns
- **Stay Informed**: Keep up with new setting options and features

❌ **Don't:**
- **Ignore Notifications**: Don't disable important alerts
- **Over-Customize**: Avoid settings that complicate your workflow
- **Share Credentials**: Don't share login information or API keys
- **Skip Security**: Don't disable important security features
- **Forget to Save**: Always save changes before leaving settings

> **💡 Tip**: Start with default settings and gradually customize as you become familiar with the system. Small, incremental changes are easier to manage than wholesale customization.

---

## Administrative Features

Administrative features in Mobilize CRM provide system-wide management capabilities for Super Admins and Office Admins to configure, monitor, and maintain the CRM system.

> **📋 Note**: Administrative features are only available to users with Super Admin or Office Admin roles. The specific features available depend on your role level.

### User Management

#### User Role Administration (Super Admin Only)

**User Roles and Permissions**:
- **Super Admin**: Full system access, all offices, configuration management
- **Office Admin**: Full access within assigned office(s), user management
- **Standard User**: Contact management, task management, communications
- **Limited User**: Read-only access to assigned data

**User Account Management**:
1. **View All Users**: Complete list of system users
2. **Role Assignment**: Change user roles and permissions
3. **Office Assignment**: Assign users to specific offices
4. **Account Status**: Activate, deactivate, or suspend user accounts
5. **Access Auditing**: Review user login history and activity

#### Office User Management (Office Admin)

**Office Team Management**:
- **Office User List**: View all users in your office
- **Role Changes**: Promote users within your office (cannot create Super Admins)
- **New User Onboarding**: Guide new team members through setup
- **Performance Monitoring**: Track team member activity and productivity

### Office Management

#### Office Configuration (Super Admin)

**Creating and Managing Offices**:
1. **Office Setup**:
   - **Name**: Official office name
   - **Code**: Short identifier for the office
   - **Location**: Physical address and contact information
   - **Status**: Active/inactive status
   - **Settings**: Office-specific configurations

2. **Multi-Office Features**:
   - **Data Segregation**: Contacts and data separated by office
   - **Cross-Office Visibility**: Configure what data offices can share
   - **Reporting Boundaries**: Office-specific vs. system-wide reporting

#### Office Settings Management

**Office-Specific Configurations**:
- **Default Pipeline Settings**: Office pipeline customizations
- **Email Templates**: Office-specific template libraries
- **Contact Visibility Rules**: Who can see what contact data
- **Task Assignment Rules**: Cross-office task assignment policies

### Pipeline Administration

#### Main Pipeline Management (Super Admin Only)

**System Pipeline Configuration**:
- **People Pipeline**: Standard individual relationship stages
  - Promotion → Information → Invitation → Confirmation → Automation
- **Church Pipeline**: Organizational relationship stages
  - Same as People Pipeline + EN42 stage
- **Stage Definitions**: Descriptions and expected activities for each stage

**Pipeline Rules and Automation**:
- **Auto-Move Rules**: Automatically advance contacts based on activity
- **Stage Requirements**: Define what must happen before stage advancement
- **Notification Rules**: Alert users about pipeline events

#### Custom Pipeline Management (Office Admin)

**Office-Specific Pipelines**:
1. **Create Custom Pipelines**: Specialized workflows for specific programs
2. **Map to Main Stages**: Link custom pipelines to main pipeline stages
3. **Stage Customization**: Define office-specific stage activities
4. **Team Training**: Ensure team understands custom pipeline usage

### Email System Administration

#### Email Template Management

**System-Wide Templates** (Super Admin):
- **Global Templates**: Available to all users across all offices
- **Template Categories**: Organize templates by purpose or audience
- **Template Approval**: Review and approve user-created templates
- **Usage Analytics**: Track template effectiveness and usage

**Office Templates** (Office Admin):
- **Office-Specific Templates**: Templates available only to office users
- **Local Customization**: Modify global templates for office use
- **Team Templates**: Create templates for team-specific activities

#### Email Integration Administration

**Gmail Integration Settings**:
- **System-Wide Permissions**: Required OAuth scopes for all users
- **Sync Policies**: Default sync settings for new users
- **Rate Limiting**: Control API usage to stay within Google limits
- **Error Monitoring**: Track and resolve integration issues

**Email Security and Compliance**:
- **Audit Logging**: Track all email activities for compliance
- **Data Retention**: Email retention policies and procedures
- **Privacy Controls**: Ensure email handling meets privacy requirements

### Task System Administration

#### Task Template Management

**Recurring Task Templates** (System-Wide):
1. **Global Templates**: Recurring tasks available to all offices
2. **Template Categories**: Organize by function or frequency
3. **Default Assignments**: Standard assignees for different task types
4. **Performance Monitoring**: Track recurring task effectiveness

**Task Automation Rules**:
- **Auto-Assignment**: Rules for automatically assigning tasks
- **Escalation Procedures**: What happens with overdue tasks
- **Notification Schedules**: Reminder timing and frequency
- **Completion Requirements**: Define what makes a task complete

#### Task Performance Analytics

**System Performance Metrics**:
- **Completion Rates**: Task completion percentages by office/user
- **Overdue Analysis**: Patterns in overdue tasks
- **Workload Distribution**: Task assignment balance
- **Productivity Trends**: Task completion trends over time

### System Monitoring and Maintenance

#### Performance Monitoring (Super Admin)

**System Health Dashboard**:
- **User Activity**: Login frequency, feature usage
- **Database Performance**: Query performance, storage usage
- **Integration Status**: Gmail, Calendar, and third-party service health
- **Error Rates**: System errors and resolution status

**Usage Analytics**:
- **Feature Adoption**: Which features are used most/least
- **User Engagement**: Activity levels by user and office
- **Data Growth**: Contact, task, and communication growth trends
- **Performance Bottlenecks**: Identify system slowdowns

#### Data Management

**Database Administration**:
- **Data Integrity**: Regular checks for data consistency
- **Backup Management**: Automated and manual backup procedures
- **Data Cleanup**: Remove outdated or duplicate records
- **Migration Tools**: Import/export capabilities for data management

**Audit and Compliance**:
- **Activity Logging**: Complete audit trail of system activities
- **Access Reporting**: Who accessed what data when
- **Compliance Monitoring**: Ensure system meets regulatory requirements
- **Data Privacy**: GDPR, CCPA, and other privacy regulation compliance

### System Configuration

#### Global Settings (Super Admin)

**System-Wide Configurations**:
- **Authentication Settings**: OAuth providers, security requirements
- **Feature Toggles**: Enable/disable system features
- **Default Values**: System-wide defaults for new records
- **API Configuration**: External integration settings

**Customization Options**:
- **Branding**: System colors, logos, organization name
- **Terminology**: Custom labels for fields and features
- **Regional Settings**: Time zones, date formats, language preferences
- **Business Rules**: Organization-specific workflow rules

#### Integration Management

**Third-Party Integrations**:
- **Google Workspace**: Gmail, Calendar, Contacts configuration
- **API Management**: External API access and rate limiting
- **Webhook Configuration**: Outbound event notifications
- **Data Synchronization**: External system data sync settings

### Backup and Disaster Recovery

#### Data Backup Systems

**Automated Backups**:
- **Schedule Configuration**: Daily, weekly, monthly backup schedules
- **Storage Management**: Backup storage location and retention
- **Validation Procedures**: Ensure backup integrity and completeness
- **Recovery Testing**: Regular recovery procedure testing

**Manual Backup Tools**:
- **On-Demand Backups**: Create backups for specific events
- **Selective Backups**: Backup specific data sets or offices
- **Export Tools**: Data export in various formats

#### Disaster Recovery Planning

**Recovery Procedures**:
- **System Restoration**: Steps to restore from backup
- **Data Recovery**: Recover specific data sets or records
- **Business Continuity**: Maintain operations during outages
- **Communication Plans**: User notification during system issues

### Security Administration

#### Access Control Management

**Permission Systems**:
- **Role-Based Access**: Define what each role can access
- **Resource Permissions**: Specific permissions for different data types
- **Office Boundaries**: Control cross-office data access
- **Feature Access**: Enable/disable features by role

**Security Monitoring**:
- **Login Monitoring**: Track unusual login patterns
- **Access Auditing**: Monitor data access patterns
- **Failed Attempts**: Track and respond to failed access attempts
- **Security Alerts**: Notifications for security events

#### Data Privacy and Compliance

**Privacy Controls**:
- **Data Anonymization**: Remove or mask personal information
- **Consent Management**: Track consent for data use
- **Right to Deletion**: Process data deletion requests
- **Data Portability**: Export user data in portable formats

### Training and Support

#### User Training Administration

**Training Program Management**:
- **Onboarding Procedures**: Standard new user training process
- **Feature Training**: Training materials for new features
- **Role-Specific Training**: Customized training by user role
- **Progress Tracking**: Monitor user training completion

**Documentation Management**:
- **Help Documentation**: Maintain system help documents
- **Video Tutorials**: Create and manage training videos
- **FAQ Management**: Keep frequently asked questions current
- **Change Documentation**: Document system changes and updates

### Best Practices for System Administration

✅ **Do:**
- **Regular Monitoring**: Check system health and performance regularly
- **User Communication**: Keep users informed about system changes
- **Security Reviews**: Regularly audit security settings and access
- **Backup Testing**: Regularly test backup and recovery procedures
- **Performance Optimization**: Monitor and optimize system performance
- **Training Updates**: Keep training materials current with system changes

❌ **Don't:**
- **Ignore Monitoring**: Don't let system issues go unaddressed
- **Skip Backups**: Never disable or skip backup procedures
- **Over-Restrict Access**: Don't make the system too difficult to use
- **Neglect Security**: Don't ignore security updates or patches
- **Forget Documentation**: Don't make changes without documentation
- **Rush Changes**: Don't implement changes without proper testing

> **💡 Tip**: Implement changes gradually and communicate with users about upcoming modifications. Regular system maintenance during off-peak hours helps ensure optimal performance.

---

## Troubleshooting

This section provides solutions to common issues users may encounter while using Mobilize CRM.

### Authentication and Login Issues

#### Google OAuth Problems

**Issue: "Access Denied" when logging in**

**Possible Causes:**
- Google account doesn't have necessary permissions
- Required OAuth scopes not granted
- Google account security settings blocking access

**Solutions:**
1. **Clear Browser Cache**: Clear cookies and cache for the CRM site
2. **Try Different Browser**: Test with Chrome, Firefox, or Safari
3. **Check Google Account**: Ensure your Google account is active and accessible
4. **Re-authorize**: Go to Settings → Gmail Integration → Reconnect
5. **Contact Admin**: Your account may need role assignment

**Issue: "Token Expired" errors**

**Solutions:**
1. **Re-authenticate**: Go to Settings → Disconnect → Reconnect Gmail
2. **Clear Stored Tokens**: Log out completely and log back in
3. **Check Permissions**: Ensure all required Google permissions are still granted

#### Permission and Access Issues

**Issue: "Access Denied" to specific features**

**Solutions:**
1. **Check User Role**: Your role determines available features
2. **Contact Office Admin**: Request role change if needed
3. **Office Assignment**: Ensure you're assigned to the correct office
4. **Data Permissions**: Some data may be restricted by office or owner

### Gmail Integration Issues

#### Email Sync Problems

**Issue: Emails not syncing from Gmail**

**Troubleshooting Steps:**
1. **Check Connection Status**:
   - Go to Settings → Gmail Integration
   - Verify "Connected" status
   - Check last sync timestamp

2. **Verify Sync Settings**:
   - Ensure sync is enabled
   - Check sync frequency settings
   - Verify contact matching preferences

3. **Test Manual Sync**:
   - Try manual sync button if available
   - Check for error messages
   - Review sync history/logs

**Issue: Duplicate emails appearing**

**Solutions:**
1. **Review Sync Settings**: Check if multiple sync modes are enabled
2. **Contact Matching**: Verify contact email addresses are correct
3. **Clear Sync History**: Reset sync and start fresh (contact admin)

#### Email Sending Issues

**Issue: Cannot send emails through CRM**

**Troubleshooting Steps:**
1. **Check Gmail Connection**: Verify Gmail integration is active
2. **Verify Permissions**: Ensure "send email" permissions are granted
3. **Test Direct Gmail**: Try sending email directly from Gmail
4. **Check Rate Limits**: May have exceeded Google API limits

**Issue: Emails sent but not recorded in CRM**

**Solutions:**
1. **Check Sync Settings**: Ensure sent emails are being synced
2. **Contact Association**: Verify recipient is a contact in CRM
3. **Manual Association**: Manually link email to contact record

### Contact Management Issues

#### Contact Data Problems

**Issue: Contacts not appearing in lists**

**Troubleshooting Steps:**
1. **Check Filters**: Remove any applied filters
2. **Verify Permissions**: Ensure you have access to view contacts
3. **Office Assignment**: Check if contacts belong to your office
4. **Status Check**: Ensure contacts are "Active" status

**Issue: Duplicate contacts**

**Solutions:**
1. **Search Before Adding**: Always search for existing contacts first
2. **Merge Contacts**: Use merge feature if available (contact admin)
3. **Standardize Data Entry**: Use consistent naming and email formats
4. **Google Contacts Sync**: Review sync settings to prevent duplicates

#### Contact Sync Issues

**Issue: Google Contacts not syncing**

**Troubleshooting Steps:**
1. **Check Sync Preferences**: Go to Settings → Contact Sync Settings
2. **Verify Permissions**: Ensure Google Contacts permission is granted
3. **Review Sync Mode**: Check if sync mode matches your needs
4. **Manual Sync**: Try forcing a sync operation

### Task Management Issues

#### Task Creation and Assignment

**Issue: Tasks not showing in task lists**

**Solutions:**
1. **Check Assignment**: Verify task is assigned to you
2. **Review Filters**: Remove status or date filters
3. **Check Due Dates**: Ensure due dates are set appropriately
4. **Office Scope**: Verify task belongs to your office

**Issue: Recurring tasks not generating**

**Troubleshooting Steps:**
1. **Check Template Status**: Ensure recurring template is active
2. **Verify Pattern**: Check recurring pattern configuration
3. **Review End Dates**: Ensure recurrence hasn't expired
4. **Background Processing**: Recurring tasks may have processing delays

#### Task Notifications

**Issue: Not receiving task notifications**

**Solutions:**
1. **Check Notification Settings**: Review notification preferences
2. **Email Notifications**: Verify email address is correct
3. **Browser Notifications**: Enable browser notification permissions
4. **Spam Filters**: Check email spam folders

### Pipeline Management Issues

#### Pipeline Stage Problems

**Issue: Cannot move contacts to different stages**

**Solutions:**
1. **Check Permissions**: Verify you can edit the specific contact
2. **Pipeline Assignment**: Ensure contact is assigned to a pipeline
3. **Stage Dependencies**: Some stages may have prerequisites
4. **Office Restrictions**: Check if stage movement is office-restricted

**Issue: Pipeline history not showing**

**Solutions:**
1. **Refresh Page**: Simple page refresh may resolve display issues
2. **Check Permissions**: Verify you can view contact history
3. **Data Processing**: History updates may have processing delays

### Communication and Email Issues

#### Communication History

**Issue: Communication history missing or incomplete**

**Troubleshooting Steps:**
1. **Check Sync Range**: Review how far back email sync is set
2. **Contact Matching**: Verify emails are properly matched to contacts
3. **Sync Status**: Check if email sync is running properly
4. **Manual Association**: Some emails may need manual contact linking

#### Template Problems

**Issue: Email templates not working**

**Solutions:**
1. **Template Access**: Verify you have access to the template
2. **Merge Fields**: Check if merge fields are correctly formatted
3. **Template Validation**: Ensure template HTML/text is valid
4. **Office Templates**: Check if template is office-specific

### Calendar Integration Issues

#### Calendar Sync Problems

**Issue: Tasks not appearing in Google Calendar**

**Solutions:**
1. **Check Calendar Settings**: Verify calendar integration is enabled
2. **Task Due Times**: Only tasks with due times sync to calendar
3. **Calendar Selection**: Ensure correct Google Calendar is selected
4. **Permissions**: Verify Google Calendar permissions are granted

**Issue: Calendar events not syncing back to CRM**

**Solutions:**
1. **Two-Way Sync**: Check if two-way sync is enabled
2. **Event Format**: CRM only syncs specific event types
3. **Manual Refresh**: Try manually refreshing calendar integration

### Performance Issues

#### Slow Loading

**Issue: CRM pages loading slowly**

**Solutions:**
1. **Clear Browser Cache**: Clear cache and cookies
2. **Check Internet Connection**: Verify stable internet connectivity
3. **Browser Extensions**: Disable ad blockers or extensions temporarily
4. **Peak Usage**: Performance may vary during high-usage times

**Issue: Timeouts or errors**

**Solutions:**
1. **Refresh Page**: Simple refresh often resolves temporary issues
2. **Try Different Browser**: Test with alternative browser
3. **Reduce Data Load**: Use filters to reduce data displayed
4. **Contact Support**: Persistent issues may require admin assistance

### Data Export and Reporting Issues

#### Export Problems

**Issue: Export files are empty or incomplete**

**Solutions:**
1. **Check Permissions**: Verify you have export permissions
2. **Data Filters**: Review applied filters that may exclude data
3. **Date Ranges**: Ensure date ranges include expected data
4. **Format Selection**: Try different export formats

**Issue: Reports show no data**

**Solutions:**
1. **View Mode**: Check if you're in the correct view mode
2. **Date Ranges**: Verify date ranges include activity periods
3. **Filters**: Remove restrictive filters
4. **Permissions**: Ensure you have access to the reported data

### Getting Additional Help

#### Self-Help Resources

**Documentation**:
- **User Guide**: This comprehensive guide
- **FAQ Section**: Common questions and answers
- **Video Tutorials**: Step-by-step visual guides
- **Help Pages**: In-system help documentation

#### Contacting Support

**Internal Support**:
1. **Office Admin**: First contact for office-specific issues
2. **Super Admin**: System-wide issues and configuration
3. **IT Support**: Technical infrastructure problems

**Support Information to Provide**:
- **Error Messages**: Exact error text or screenshots
- **Steps to Reproduce**: What you were doing when the issue occurred
- **Browser/Device**: What browser and device you're using
- **Timing**: When the issue started occurring
- **User Role**: Your role and office assignment

#### Escalation Process

1. **Try Self-Help**: Consult documentation and this troubleshooting guide
2. **Contact Office Admin**: For office-level issues
3. **Super Admin**: For system-wide or complex issues
4. **External Support**: For technical infrastructure or integration issues

### Prevention Best Practices

✅ **Preventive Measures**:
- **Regular Updates**: Keep browser updated
- **Consistent Data Entry**: Use standardized formats for names, emails
- **Regular Sync Checks**: Monitor integration status regularly
- **Backup Important Data**: Export critical data regularly
- **Training Updates**: Stay current with system training

❌ **Avoid Common Mistakes**:
- **Multiple Browser Tabs**: Can cause sync conflicts
- **Shared Accounts**: Don't share login credentials
- **Ignore Error Messages**: Address errors promptly
- **Skip Updates**: Don't ignore system update notifications
- **Bulk Changes Without Backup**: Always backup before major changes

> **💡 Tip**: Most issues can be resolved by logging out completely, clearing browser cache, and logging back in. This refreshes all connections and resolves many common problems.

---

## Frequently Asked Questions

### General System Questions

**Q: What is Mobilize CRM designed for?**
A: Mobilize CRM is specifically designed for non-profit organizations, churches, and missionary organizations to manage relationships with individuals (people) and organizations (churches) through customizable pipeline stages. It tracks the progression of relationships from initial contact through long-term engagement.

**Q: Do I need to create a separate account for Mobilize CRM?**
A: No, Mobilize CRM uses Google OAuth for authentication. You log in with your existing Google account, and the system automatically creates your user profile and associated Person record.

**Q: What happens to my data if I leave the organization?**
A: Your user account can be deactivated by administrators, but the contacts and data you created remain in the system for organizational continuity. Your Person record remains active for historical reference.

### Contact Management

**Q: What's the difference between a Person and a Church in the system?**
A: Both People and Churches are contacts, but they serve different purposes:
- **Person**: Individual contacts with personal information, church relationships, and individual pipeline tracking
- **Church**: Organizational contacts with institutional information, leadership details, and church-specific pipeline stages (including EN42)

**Q: Can one person be associated with multiple churches?**
A: Yes, people can have relationships with multiple churches through the ChurchMembership system. Each relationship can have different roles and status (active, inactive, former).

**Q: How do I avoid creating duplicate contacts?**
A: Always search for existing contacts before creating new ones. Use the search function with email addresses, names, or phone numbers. The system will show potential matches to help prevent duplicates.

**Q: Can I import my existing contacts from another system?**
A: Contact your system administrator about data import capabilities. The system has import tools, but they typically require administrative access to ensure data quality and prevent duplicates.

### Pipeline Management

**Q: What do the different pipeline stages mean?**
A: The standard pipeline stages represent relationship progression:
- **Promotion**: Initial awareness and interest
- **Information**: Detailed information sharing and education
- **Invitation**: Formal invitation to participate
- **Confirmation**: Commitment finalization
- **Automation**: Ongoing relationship management
- **EN42** (Churches only): Enhanced engagement level

**Q: Can I skip pipeline stages?**
A: While technically possible, it's not recommended. The pipeline stages represent a logical progression. Skipping stages may result in missed opportunities or inadequate relationship development.

**Q: How often should I update pipeline stages?**
A: Update pipeline stages after significant interactions or developments. This could be after meetings, email exchanges, decisions, or any activity that represents progress in the relationship.

**Q: What happens if a contact doesn't progress through the pipeline?**
A: Contacts can remain in any stage indefinitely. Use notes and task reminders to document reasons for delays and plan follow-up activities. Some contacts may naturally exit the pipeline if they're no longer interested or appropriate.

### Task Management

**Q: Can I assign tasks to people in other offices?**
A: This depends on your role:
- **Super Admin**: Can assign tasks across all offices
- **Office Admin**: Can assign within their office(s)
- **Standard User**: Can typically only assign within their office
- **Limited User**: Usually cannot assign tasks to others

**Q: What happens to recurring tasks when I'm away?**
A: Recurring tasks continue to generate according to their schedule. If you'll be away for extended periods, consider:
- Temporarily disabling recurring task templates
- Asking colleagues to cover critical recurring tasks
- Adjusting recurrence patterns for your schedule

**Q: Can I modify a recurring task after it's created?**
A: You can modify individual task instances, but changes to the recurring template only affect future tasks. If you need to modify all future occurrences, edit the recurring task template.

### Email Integration

**Q: Will connecting Gmail give the CRM access to all my emails?**
A: By default, the system uses "Contacts Only" sync mode, which only syncs emails to/from people in your CRM. You can choose to sync all emails, but this is not recommended for privacy and performance reasons.

**Q: Can I disconnect Gmail integration without losing data?**
A: Yes, disconnecting Gmail stops future synchronization but doesn't delete emails already synced to the CRM. However, you won't be able to send emails through the CRM until you reconnect.

**Q: Why aren't all my emails syncing to the CRM?**
A: Check your sync settings:
- **Contacts Only mode**: Only emails from CRM contacts sync
- **Date Range**: May only sync recent emails
- **Contact Matching**: Ensure contact email addresses are accurate
- **Sync Frequency**: May not have synced recently

### Permissions and Access

**Q: Why can't I see all the contacts in the system?**
A: Your data access depends on your role and office assignment:
- **Super Admin**: Sees all data across all offices
- **Office Admin**: Sees all data within assigned office(s)
- **Standard User**: Sees their own contacts plus office churches
- **Limited User**: Has read-only access to assigned data

**Q: Can I change my own user role?**
A: No, user roles must be changed by administrators:
- **Super Admin**: Can change any user's role
- **Office Admin**: Can change roles within their office (except cannot create Super Admins)
- **Standard/Limited Users**: Cannot change roles

**Q: What if I need access to data in another office?**
A: Contact your system administrator. They can:
- Add you to multiple offices
- Change your role if appropriate
- Provide temporary access for specific projects

### Google Integration

**Q: What Google permissions does Mobilize CRM need?**
A: The system requests:
- **Basic Profile**: Name, email for account identification
- **Gmail**: Compose, send, and read emails
- **Google Contacts**: Sync contact information
- **Google Calendar**: Create and sync calendar events

**Q: Can I use Mobilize CRM without connecting Google services?**
A: You need Google authentication to log in, but you can disable specific integrations:
- **Gmail sync** can be turned off (you won't see email history)
- **Calendar sync** can be disabled (tasks won't appear in calendar)
- **Contact sync** can be set to "disabled" mode

**Q: What happens if Google changes their API or permissions?**
A: System administrators monitor Google API changes and update the system as needed. You may occasionally need to re-authorize permissions when Google updates their systems.

### Data and Privacy

**Q: Who can see my contact data?**
A: Data visibility depends on several factors:
- **Your Role**: Determines base access level
- **Office Assignment**: Office-based data segregation
- **Contact Ownership**: Some systems restrict to contact creators
- **Administrative Access**: Admins may have broader access for management

**Q: Can I export my data from the system?**
A: Export capabilities depend on your role:
- **Reporting Access**: Generate reports for data you can view
- **Personal Data Export**: Export contacts and tasks you've created
- **Administrative Export**: Full data export (admin roles only)

**Q: Is my data secure in Mobilize CRM?**
A: The system implements multiple security measures:
- **Google OAuth**: Secure authentication
- **Role-Based Access**: Data access controls
- **Audit Logging**: Activity tracking
- **Data Encryption**: Secure data transmission and storage

### Technical Issues

**Q: What browsers work best with Mobilize CRM?**
A: Recommended browsers include:
- **Chrome**: Optimal performance and compatibility
- **Firefox**: Good compatibility
- **Safari**: Works well on Mac systems
- **Edge**: Compatible but may have minor differences

**Q: Can I use Mobilize CRM on my mobile device?**
A: The system is web-based and works on mobile browsers, though the interface is optimized for desktop use. Key functions like viewing contacts, tasks, and communications work well on mobile devices.

**Q: What should I do if the system is running slowly?**
A: Try these steps:
1. Clear your browser cache and cookies
2. Close unnecessary browser tabs
3. Check your internet connection
4. Try a different browser
5. Contact your administrator if problems persist

**Q: Can I use Mobilize CRM offline?**
A: The system requires internet connectivity for most functions. Some cached data may be available offline temporarily, but full functionality requires an active internet connection.

### Training and Support

**Q: Where can I get training on using the system?**
A: Training resources include:
- **This User Guide**: Comprehensive documentation
- **Office Admin**: Your first contact for training needs
- **System Help Pages**: Built-in help documentation
- **Video Tutorials**: Step-by-step visual guides (if available)

**Q: Who should I contact when I have problems?**
A: Follow this escalation path:
1. **Self-Help**: Check this guide and system help pages
2. **Office Admin**: For office-specific issues and training
3. **Super Admin**: For system-wide issues
4. **Technical Support**: For infrastructure or integration problems

**Q: How often is the system updated?**
A: System updates vary but typically include:
- **Regular Updates**: Bug fixes and minor improvements
- **Feature Releases**: New functionality and enhancements
- **Security Updates**: Applied as needed for security
- **Integration Updates**: When external services change

**Q: Can I suggest new features or improvements?**
A: Yes! Feature requests can be submitted through:
- **Office Admin**: Collect office-wide feedback
- **Super Admin**: Submit system-wide suggestions
- **User Feedback**: Use any feedback mechanisms provided in the system

---

## Conclusion

Congratulations! You've completed the Mobilize CRM User Guide. This comprehensive resource covers all aspects of using the system effectively, from basic contact management to advanced administrative features.

### Quick Reference Summary

**Key Features at a Glance:**
- **Contact Management**: People and Church records with comprehensive relationship tracking
- **Pipeline System**: Structured relationship progression through defined stages
- **Task Management**: Assignment, tracking, and recurring task automation
- **Gmail Integration**: Seamless email synchronization and communication tracking
- **Calendar Integration**: Task and meeting synchronization with Google Calendar
- **Reporting**: Comprehensive analytics and data export capabilities
- **Multi-Office Support**: Segregated data with appropriate access controls

**Getting Started Checklist:**
- ✅ Complete initial login with Google OAuth
- ✅ Set up Gmail integration in Settings
- ✅ Configure notification preferences
- ✅ Customize dashboard widgets
- ✅ Create your first contact
- ✅ Set up recurring tasks for regular activities
- ✅ Explore pipeline management features

### Best Practices Reminder

**Daily Workflow:**
1. **Check Dashboard**: Review pending tasks and recent activity
2. **Process Tasks**: Complete due items and update progress
3. **Update Contacts**: Log interactions and update pipeline stages
4. **Review Communications**: Process new emails and plan follow-ups

**Weekly Maintenance:**
1. **Pipeline Review**: Assess contact progression and plan next steps
2. **Task Planning**: Create upcoming tasks and adjust recurring patterns
3. **Data Cleanup**: Update contact information and resolve duplicates
4. **Performance Review**: Check completion rates and relationship health

**Success Tips:**
- **Stay Consistent**: Regular data entry and updates improve system value
- **Use Integration**: Leverage Gmail and Calendar sync for efficiency  
- **Communicate Effectively**: Use email templates and signatures professionally
- **Monitor Progress**: Use reports to track relationship development
- **Ask for Help**: Don't hesitate to contact administrators with questions

### System Evolution

Mobilize CRM continues to evolve based on user feedback and organizational needs. Stay informed about:
- **New Feature Announcements**: Watch for system updates and enhancements
- **Training Opportunities**: Participate in ongoing training for new features
- **Best Practice Sharing**: Learn from successful users in your organization
- **Feedback Opportunities**: Contribute suggestions for system improvements

### Final Notes

This User Guide represents the system as of February 2025. While we strive to keep documentation current, specific features and interfaces may evolve over time. Always refer to the in-system help pages for the most current information about specific features.

Remember that Mobilize CRM is more than just a database—it's a relationship management tool designed to help you build and maintain meaningful connections with individuals and organizations in support of your mission.

**Thank you for using Mobilize CRM!**

For additional support, contact your Office Administrator or System Administrator.

---

*Document Version: 1.0*  
*Last Updated: February 2025*  
*© 2025 Mobilize CRM - All Rights Reserved*