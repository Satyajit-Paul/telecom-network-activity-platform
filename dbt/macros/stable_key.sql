{% macro stable_key(fields) -%}
    md5(
        {%- for field in fields -%}
            coalesce(cast({{ field }} as text), '<null>')
            {%- if not loop.last %} || '|' || {% endif -%}
        {%- endfor -%}
    )
{%- endmacro %}
