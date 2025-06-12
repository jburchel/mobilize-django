# Mobilize CRM Template System Guide

## Overview

The frontend implementation is now complete with a comprehensive template system that provides:

- ✅ Enhanced base template with common elements
- ✅ Template inheritance hierarchy with specialized layouts  
- ✅ Reusable partial components
- ✅ Comprehensive template blocks for content areas
- ✅ Mobile-responsive layouts and CSS system

## Template Hierarchy

### Base Template (`templates/base.html`)
The foundation template that includes:
- Brand colors and design system CSS variables
- Navigation sidebar with proper Django URL integration
- User profile dropdown with authentication info
- Responsive mobile navigation
- Comprehensive template blocks

### Layout Templates (`templates/layouts/`)

#### 1. List Layout (`list_layout.html`)
For pages displaying lists of items (contacts, churches, tasks)
```django
{% extends 'layouts/list_layout.html' %}
{% block custom_filters %}
    <!-- Add custom filter fields -->
{% endblock %}
```

#### 2. Form Layout (`form_layout.html`)
For create/edit forms with consistent styling
```django
{% extends 'layouts/form_layout.html' %}
{% block form_content %}
    <!-- Form fields with automatic validation -->
{% endblock %}
```

#### 3. Detail Layout (`detail_layout.html`)
For individual item detail views
```django
{% extends 'layouts/detail_layout.html' %}
{% block main_content %}
    <!-- Detail sections and information -->
{% endblock %}
```

#### 4. Dashboard Layout (`dashboard_layout.html`)
For dashboard and analytics pages
```django
{% extends 'layouts/dashboard_layout.html' %}
{% block dashboard_content %}
    <!-- Charts, metrics, and widgets -->
{% endblock %}
```

## Reusable Components (`templates/partials/`)

### 1. Metric Card (`metric_card.html`)
```django
{% include 'partials/metric_card.html' with title="People" value="150" subtitle="+12 this week" icon="fas fa-users" color="primary" href="/people/" %}
```

### 2. Data Table (`data_table.html`)
```django
{% include 'partials/data_table.html' with headers=table_headers rows=table_data searchable=True sortable=True %}
```

### 3. Form Field (`form_field.html`)
```django
{% include 'partials/form_field.html' with field=form.name label="Full Name" required=True %}
```

### 4. Alert/Notification (`alert.html`)
```django
{% include 'partials/alert.html' with type="success" message="Operation completed!" dismissible=True %}
```

### 5. Modal Dialog (`modal.html`)
```django
{% include 'partials/modal.html' with modal_id="confirmModal" title="Confirm Action" body="Are you sure?" %}
```

### 6. Confirmation Dialog (`confirm_dialog.html`)
```django
{% include 'partials/confirm_dialog.html' with title="Delete Item" message="Confirm deletion?" action_url="/delete/" %}
```

### 7. Loading States (`loading_state.html`)
```django
{% include 'partials/loading_state.html' with type="spinner" message="Loading..." %}
{% include 'partials/loading_state.html' with type="skeleton" rows=3 %}
```

### 8. Empty State (`empty_state.html`)
```django
{% include 'partials/empty_state.html' with icon="fas fa-users" title="No contacts yet" action_text="Add Contact" action_url="/add/" %}
```

### 9. Breadcrumb (`breadcrumb.html`)
```django
{% include 'partials/breadcrumb.html' with items=breadcrumb_items %}
```

### 10. Page Header (`page_header.html`)
```django
{% include 'partials/page_header.html' with title="Dashboard" subtitle="Welcome back!" %}
```

## CSS System

### Design Tokens (`static/css/base.css`)
- Brand colors following Crossover Global guidelines
- 8px spacing grid system
- Typography hierarchy with Cronos Pro fallbacks
- Consistent shadows, borders, and transitions

### Responsive System (`static/css/responsive.css`)
- Mobile-first approach
- Breakpoints: 576px, 768px, 992px, 1200px, 1400px
- Touch-optimized interfaces
- Print styles
- Accessibility enhancements

## Template Blocks Structure

### Base Template Blocks
```django
{% block title %}{% endblock %}           <!-- Page title -->
{% block extra_css %}{% endblock %}       <!-- Additional CSS -->
{% block page_header %}{% endblock %}     <!-- Page header area -->
{% block page_title %}{% endblock %}      <!-- Page title -->
{% block page_subtitle %}{% endblock %}   <!-- Page subtitle -->
{% block page_actions %}{% endblock %}    <!-- Action buttons -->
{% block messages %}{% endblock %}        <!-- Alert messages -->
{% block pre_content %}{% endblock %}     <!-- Before main content -->
{% block content %}{% endblock %}         <!-- Main content -->
{% block post_content %}{% endblock %}    <!-- After main content -->
{% block footer_content %}{% endblock %}  <!-- Footer area -->
{% block extra_js %}{% endblock %}        <!-- Additional JavaScript -->
```

### Layout-Specific Blocks
Each layout template provides additional specialized blocks for maximum flexibility.

## Usage Examples

### Creating a New List Page
```django
{% extends 'layouts/list_layout.html' %}

{% block page_title %}People{% endblock %}
{% block item_name %}Person{% endblock %}
{% block add_url %}{% url 'contacts:person_create' %}{% endblock %}

{% block custom_filters %}
    <div class="col-md-3">
        <label for="pipeline" class="form-label">Pipeline Stage</label>
        <select class="form-select" id="pipeline">
            <option value="">All Stages</option>
            {% for stage in pipeline_stages %}
                <option value="{{ stage }}">{{ stage }}</option>
            {% endfor %}
        </select>
    </div>
{% endblock %}
```

### Creating a New Form Page
```django
{% extends 'layouts/form_layout.html' %}

{% block page_title %}Add Person{% endblock %}
{% block cancel_url %}{% url 'contacts:person_list' %}{% endblock %}

{% block form_content %}
    {% for field in form %}
        {% include 'partials/form_field.html' with field=field %}
    {% endfor %}
{% endblock %}
```

### Creating a New Detail Page
```django
{% extends 'layouts/detail_layout.html' %}

{% block page_title %}{{ person.get_full_name }}{% endblock %}
{% block edit_url %}{% url 'contacts:person_edit' person.pk %}{% endblock %}

{% block main_content %}
    <div class="row">
        <div class="col-md-6">
            <dt>Email</dt>
            <dd><a href="mailto:{{ person.email }}">{{ person.email }}</a></dd>
        </div>
        <div class="col-md-6">
            <dt>Phone</dt>
            <dd><a href="tel:{{ person.phone }}">{{ person.phone }}</a></dd>
        </div>
    </div>
{% endblock %}
```

## Mobile Responsiveness Features

- **Responsive Navigation**: Collapsible sidebar on mobile devices
- **Touch-Optimized**: Minimum 44px touch targets
- **Adaptive Typography**: Fluid font sizing using clamp()
- **Flexible Layouts**: CSS Grid and Flexbox for responsive components
- **Mobile Tables**: Alternative mobile-friendly table layouts
- **Breakpoint Utilities**: Mobile-only/desktop-only display classes

## Accessibility Features

- **ARIA Labels**: Proper labeling for screen readers
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Management**: Visible focus indicators
- **Color Contrast**: WCAG 2.1 AA compliant colors
- **Reduced Motion**: Respects user motion preferences
- **High Contrast**: Support for high contrast mode

## Next Steps

The frontend template system is now ready for use. To implement in existing views:

1. Update view templates to extend appropriate layout templates
2. Move inline styles to the CSS system
3. Replace hardcoded components with partial includes
4. Test responsive behavior across devices
5. Validate accessibility compliance

This template system provides a solid foundation for consistent, maintainable, and accessible UI components throughout the Mobilize CRM application.