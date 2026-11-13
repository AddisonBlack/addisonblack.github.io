# addisonblack.github.io

Personal portfolio for Addison Black, Power BI developer and data analyst.
Plain HTML, CSS and a little vanilla JavaScript. No frameworks, no build step.

Live site: https://addisonblack.github.io/

## Structure

```
index.html                 Home page (hero, skills, projects, DAX library, about, contact)
projects/retail-sales.html Case study page; copy it as a template for new projects
css/styles.css             The one shared stylesheet (colors are CSS variables at the top)
js/main.js                 Mobile menu toggle
assets/img/                Dashboard screenshots, thumbnails, social preview image
assets/resume.pdf          Your resume (add this file; the Resume buttons link to it)
.nojekyll                  Tells GitHub Pages to serve files as-is
```

## Finding placeholders

Everything that needs your real content is wrapped in `[square brackets]`.
Search the project for `[` to find them all, including links like
`mailto:[your-email@example.com]` and `https://github.com/AddisonBlack/[retail-sales-repo]`.

## Previewing locally

Open `index.html` in a browser. Or, to serve it the way GitHub Pages will:

```
python3 -m http.server 8000
```

then visit http://localhost:8000.

## Adding a new project

1. Copy `projects/retail-sales.html` to a new file, e.g. `projects/customer-retention.html`.
2. In the new file, update the `<title>`, the meta description, the Open Graph tags
   (`og:title`, `og:description`, `og:url`, `og:image`), the H1, and every `[bracketed]` item.
3. Put screenshots in `assets/img/` and swap the placeholder `<div>`s for `<img>` tags.
   Each placeholder has a comment showing the exact `<img>` to use. Always write useful `alt` text.
4. Update the "Next project" link at the bottom of the page.
5. In `index.html`, point that project card's "Read case study →" link at the new page,
   and replace its CSS thumbnail with `<img class="thumb" src="assets/img/..." alt="...">`.
6. To add a fourth card, copy one `<li>…</li>` block in the projects grid.

## Editing the design

Colors, fonts and spacing are CSS custom properties at the top of `css/styles.css`.
The stylesheet is split into numbered, commented sections (header, hero, projects,
DAX library, case study, media queries, and so on).

Contrast notes: `--sage` is decorative only (too light for text). Use `--sage-dark`
for small secondary text on cream.
