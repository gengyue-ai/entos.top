<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html lang="zh-CN">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title><xsl:value-of select="/rss/channel/title"/> - RSS Feed</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Noto Sans SC', sans-serif; background: #f8fafc; color: #0f172a; line-height: 1.6; }
    .header { max-width: 720px; margin: 0 auto; padding: 48px 24px 24px; }
    .header h1 { font-size: 28px; font-weight: 700; }
    .header a { color: #2563eb; text-decoration: none; }
    .header a:hover { text-decoration: underline; }
    .header p { color: #64748b; font-size: 14px; margin-top: 6px; }
    .list { max-width: 720px; margin: 0 auto; padding: 0 24px 80px; display: flex; flex-direction: column; gap: 0; background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 10px; overflow: hidden; }
    .item { display: block; padding: 20px 24px; border-bottom: 1px solid #f1f5f9; text-decoration: none; color: inherit; transition: background .1s; }
    .item:last-child { border-bottom: none; }
    .item:hover { background: #f8fafc; }
    .item h3 { font-size: 16px; font-weight: 600; color: #0f172a; margin-bottom: 4px; }
    .item p { font-size: 13px; color: #64748b; line-height: 1.6; margin-bottom: 6px; }
    .item .date { font-size: 12px; color: #94a3b8; }
    .footer { max-width: 720px; margin: 0 auto; padding: 24px; text-align: center; font-size: 13px; color: #94a3b8; }
  </style>
</head>
<body>
  <div class="header">
    <h1><a href="/"><xsl:value-of select="/rss/channel/title"/></a></h1>
    <p><xsl:value-of select="/rss/channel/description"/></p>
  </div>

  <div class="list">
    <xsl:for-each select="/rss/channel/item">
      <a class="item" href="{link}">
        <h3><xsl:value-of select="title"/></h3>
        <p><xsl:value-of select="description"/></p>
        <div class="date"><xsl:value-of select="pubDate"/></div>
      </a>
    </xsl:for-each>
  </div>

  <div class="footer">
    <xsl:value-of select="/rss/channel/copyright"/>
  </div>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
