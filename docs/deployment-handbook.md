# entos.top 部署手册

## 一、服务器信息

| 项目 | 值 |
|------|-----|
| IP | 47.115.50.15 |
| 配置 | 2核2G |
| 系统 | Ubuntu 22.04 |
| WEB | Nginx |

## 二、目录结构

### 源代码（唯一路径）
```
/root/entos.top/
  ├── src/pages/           ← 页面源文件 (.astro)
  │   ├── index.astro      ← 首页
  │   ├── blog.astro       ← 文章列表
  │   └── blog/            ← 文章详情页
  │       ├── *.astro
  │       └── firecrawl-mcp-plan.astro
  ├── src/layouts/         ← 布局模板
  ├── dist/                ← 构建输出（自动生成）
  ├── package.json
  └── node_modules/
```

> ⚠️ 注意：只有 `/root/entos.top/` 是有效路径。
> `/root/ertos.top/` 是旧克隆，已删除。

### 部署目录
```
/var/www/entos/
  ├── index.html
  ├── blog/
  │   ├── index.html       ← 文章列表
  │   └── firecrawl-mcp-plan/
  │       └── index.html   ← 文章页面
  └── ...其他页面
```

## 三、发布流程

```
修改源码 → 构建 → 部署
```

**Step 1: 修改**
```
cd /root/entos.top
vim src/pages/xxx.astro
```

**Step 2: 构建**
```
npm run build
```
构建产物在 `dist/` 目录。

**Step 3: 部署**
```
cp -r dist/* /var/www/entos/
```

**完整流程（一行）：**
```
cd /root/entos.top && npm run build && cp -r dist/* /var/www/entos/
```

## 四、文章发布 Checklist

添加一篇新文章：

1. 在 `src/pages/blog/` 创建 `xxx.astro`
2. 在 `src/pages/blog.astro` 的 `articles` 数组添加条目
3. 如果新文章标签不在已有分类中，在 `categories` 数组添加新分类
4. 在 `src/pages/index.astro` 的 `articles` 数组添加条目
5. `npm run build && cp -r dist/* /var/www/entos/`

## 五、有效路径一览

```
/root/entos.top/                    ← 唯一源码目录
/root/entos.top/dist/                ← 构建输出
/var/www/entos/                      ← Nginx 部署目录
```

**所有其他路径均无效（已清理）：**
```
/root/ertos.top/                     ← 已删除
```

## 六、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 修改了源码但页面没变 | 忘记 build 或 deploy | 执行完整流程 |
| 文章列表不显示 | 文章分类不在 categories 中 | 添加分类 |
| 首页不显示 | 未在 index.astro 添加条目 | 添加到 articles 数组 |
| 日期不对 | 只改了一处 | 检查 3 个文件：文章页 + blog.astro + index.astro |
