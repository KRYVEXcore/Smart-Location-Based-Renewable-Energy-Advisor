import { createElement, Fragment, type ReactNode } from 'react'

// A tiny, safe renderer for the little formatting the advisor uses: **bold** and
// "- " / "* " list lines. It never parses HTML: everything is returned as React
// text nodes (which React escapes), so markup in a model reply is shown as text.

export interface RichTextPart {
  text: string
  bold: boolean
}

export function splitBold(text: string): RichTextPart[] {
  const parts: RichTextPart[] = []
  let last = 0
  for (const match of text.matchAll(/\*\*([^*\n]+?)\*\*/g)) {
    const start = match.index ?? 0
    if (start > last) parts.push({ text: text.slice(last, start), bold: false })
    parts.push({ text: match[1] ?? '', bold: true })
    last = start + match[0].length
  }
  if (last < text.length) parts.push({ text: text.slice(last), bold: false })
  return parts
}

// "- item" and "* item" become "• item" so list lines read cleanly without markdown markers.
function tidyListMarkers(text: string): string {
  return text.replace(/^(\s*)[-*]\s+/gm, '$1• ')
}

// Line breaks are kept as "\n" characters; the chat bubble renders them with whitespace-pre-wrap.
export function renderRichText(text: string): ReactNode {
  const parts = splitBold(tidyListMarkers(text))
  return createElement(
    Fragment,
    null,
    ...parts.map((part, index) =>
      part.bold ? createElement('strong', { key: index, className: 'font-semibold' }, part.text) : part.text,
    ),
  )
}
