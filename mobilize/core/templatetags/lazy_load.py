from django import template
from django.utils.safestring import mark_safe
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def lazy_image(src, alt='', css_class='', width=None, height=None, placeholder=None):
    """
    Template tag for lazy loading images.
    
    Usage:
        {% lazy_image 'path/to/image.jpg' alt='Description' css_class='img-fluid' %}
    """
    # Use a data URI placeholder if none provided
    if not placeholder:
        if width and height:
            # Create SVG placeholder with aspect ratio
            svg_placeholder = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg"><rect width="100%" height="100%" fill="#f0f0f0"/></svg>'
            placeholder = f'data:image/svg+xml;base64,{svg_placeholder.encode("base64").decode()}'
        else:
            # 1x1 transparent pixel
            placeholder = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
    
    # Build image tag
    attrs = []
    attrs.append(f'src="{placeholder}"')
    attrs.append(f'data-lazy="{src}"')
    attrs.append(f'alt="{alt}"')
    
    if css_class:
        attrs.append(f'class="{css_class}"')
    
    if width:
        attrs.append(f'width="{width}"')
    
    if height:
        attrs.append(f'height="{height}"')
    
    img_tag = f'<img {" ".join(attrs)}>'
    
    # Add noscript fallback
    noscript = f'<noscript><img src="{src}" alt="{alt}"></noscript>'
    
    return mark_safe(img_tag + noscript)


@register.simple_tag
def lazy_background(selector, image_url, placeholder_color='#f0f0f0'):
    """
    Template tag for lazy loading background images.
    
    Usage:
        {% lazy_background '.hero-section' 'path/to/bg-image.jpg' %}
    """
    script = f'''
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const element = document.querySelector('{selector}');
        if (element) {{
            // Set placeholder background
            element.style.backgroundColor = '{placeholder_color}';
            
            // Create image to preload
            const img = new Image();
            img.onload = function() {{
                element.style.backgroundImage = 'url(' + this.src + ')';
                element.classList.add('bg-loaded');
            }};
            img.src = '{image_url}';
        }}
    }});
    </script>
    '''
    
    return mark_safe(script)


@register.filter
def add_lazy_loading(html_content):
    """
    Filter to automatically add lazy loading to all images in HTML content.
    
    Usage:
        {{ content|add_lazy_loading }}
    """
    import re
    
    def replace_img(match):
        img_tag = match.group(0)
        
        # Skip if already has lazy loading
        if 'data-lazy' in img_tag:
            return img_tag
        
        # Extract src
        src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
        if not src_match:
            return img_tag
        
        src = src_match.group(1)
        
        # Replace src with placeholder and add data-lazy
        placeholder = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        new_img_tag = img_tag.replace(
            f'src="{src}"', 
            f'src="{placeholder}" data-lazy="{src}"'
        ).replace(
            f"src='{src}'", 
            f'src="{placeholder}" data-lazy="{src}"'
        )
        
        return new_img_tag
    
    # Replace all img tags
    pattern = r'<img[^>]+>'
    modified_html = re.sub(pattern, replace_img, html_content)
    
    return mark_safe(modified_html)