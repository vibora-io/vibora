### Template Syntax

VTE syntax is basically split between two things: Tags and Expressions.

```html
<html>
    <head>
        <title> {{ title }} </title>
    </head>
    <body>
        <ul>
            {% for user in users %}
                <li> {{ user.name}} </li>
            {% endfor %}
        </ul>
    </body>
</html>
```

1) Expressions are delimited by "{ { variable_name } }" and they are used to print data.

2) Tags are delimited by "{ % tag_name % }" and they are used to express intents like loops, conditionals, etc.

> There are many default tags and you can create your own too
by adding an extension, you can also customize the markers so instead of
"{%" you could use "#[" or whatever do you think it's best.
