# Admin Section Implementation Plan

## Overview
Create a comprehensive admin system with role-based access control, admin dashboard, and management capabilities for the Fantasy Football Assistant.

## 1. Database Schema Updates

### Add Admin Fields to User Model
- Add `is_admin` boolean field (default: False)
- Add `is_superadmin` boolean field (default: False) 
- Add `admin_notes` text field for admin-specific notes
- Add `permissions` JSON field for granular permissions

### Create Admin Activity Log Table
- Track all admin actions for audit purposes
- Fields: id, admin_id, action, target_type, target_id, details, timestamp

## 2. Backend Implementation

### Update User Model (`src/models/user.py`)
- Add admin-related fields
- Add methods for checking permissions

### Create Admin Dependencies (`src/utils/dependencies.py`)
- `get_admin_user()` - Verify user is admin
- `get_superadmin_user()` - Verify user is superadmin
- Permission checking decorators

### Create Admin API Router (`src/api/admin.py`)
- User management endpoints
- System statistics endpoints
- Configuration management
- Activity logs
- Database maintenance tools

### Key Admin Endpoints:
- `GET /api/admin/users` - List all users
- `PUT /api/admin/users/{id}` - Update user (including admin status)
- `DELETE /api/admin/users/{id}` - Delete user
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/logs` - Admin activity logs
- `POST /api/admin/broadcast` - Send notifications
- `GET /api/admin/config` - System configuration
- `POST /api/admin/maintenance` - Database maintenance tasks

## 3. Frontend Implementation

### Admin Pages Structure
```
/admin
  /dashboard - Overview and stats
  /users - User management
  /leagues - League management
  /content - Content moderation
  /logs - Activity logs
  /settings - System settings
```

### Components to Create:
1. `AdminLayout.tsx` - Admin-specific layout with sidebar
2. `AdminDashboard.tsx` - Statistics and overview
3. `UserManagement.tsx` - CRUD operations for users
4. `AdminGuard.tsx` - Route protection component
5. `ActivityLog.tsx` - View admin actions
6. `SystemSettings.tsx` - Configure system parameters

### Update Navigation
- Add admin link in MainLayout (only visible to admins)
- Create separate admin navigation menu

## 4. Security Implementation

### Access Control Levels:
1. **Regular User**: Standard access
2. **Admin**: Can manage users, view stats, moderate content
3. **Superadmin**: Full system access, can create other admins

### Security Features:
- JWT token includes admin role
- Admin actions logged with IP and timestamp
- Rate limiting for admin endpoints
- Two-factor authentication for admin accounts (optional)

## 5. Admin Features

### User Management
- View all users with filters
- Edit user details and permissions
- Suspend/activate accounts
- Reset passwords
- View user activity

### System Monitoring
- Active users count
- API usage statistics
- Database size and performance
- Error logs
- WebSocket connections

### Content Management
- Moderate user-generated content
- Manage AI responses
- Configure scoring systems

### League Management
- View all leagues across platforms
- Debug sync issues
- Manual data corrections

## 6. Database Migration

### Create migration script:
- Add admin fields to users table
- Create admin_activity_logs table
- Add indexes for performance
- Seed initial admin user

## 7. Implementation Order

1. Update User model with admin fields
2. Create database migration
3. Implement admin dependencies and auth
4. Create admin API endpoints
5. Build AdminGuard component
6. Create admin dashboard page
7. Implement user management
8. Add activity logging
9. Create system settings page
10. Update main navigation

## 8. Testing Considerations

- Unit tests for admin permissions
- Integration tests for admin endpoints
- E2E tests for admin workflows
- Security penetration testing

## 9. Initial Admin Setup

Create a CLI command to create the first admin:
```bash
python -m src.scripts.create_admin --email admin@example.com --username admin
```

This plan provides a robust admin system with proper security, audit trails, and comprehensive management capabilities.