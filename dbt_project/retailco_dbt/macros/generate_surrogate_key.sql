{% macro generate_surrogate_key(cols) %}

md5(
    concat(
        {% for col in cols %}
            coalesce(cast({{ col }} as text), '')
            {% if not loop.last %}
                , '|',
            {% endif %}
        {% endfor %}
    )
)

{% endmacro %}