# Interaction API 文档

## 1. 点赞接口

- URL: `/interaction/like/`
- 方法: `POST`
- 请求参数:
  - `article_id` (必填) - 文章 ID
- 响应:
```json
{
  "liked": true,
  "created": true,
  "like_count": 42
}
```

## 2. 收藏夹接口

- URL: `/interaction/folders/`
- 方法: `GET` 获取用户收藏夹列表
- 方法: `POST` 创建收藏夹
  - `name` (必填)
  - `description`
  - `is_public`
  - `allow_duplicates`

## 3. 收藏文章

- URL: `/interaction/items/`
- 方法: `POST`
- 参数:
  - `folder_id`
  - `article_id`
  - `note`

## 4. 删除收藏

- URL: `/interaction/items/<id>/`
- 方法: `DELETE`

## 5. 收藏夹分享

- URL: `/interaction/share/<token>/`
- 方法: `GET`
- 说明: 公开访问收藏夹

## 6. 排行榜

- URL: `/interaction/leaderboard/`
- 方法: `GET`
- 可选参数:
  - `since=2024-01-01T00:00:00` (ISO 时间)

## 7. 收藏夹详情

- URL: `/interaction/folders/<id>/`
- 方法: `GET` 返回单个收藏夹信息
- 方法: `POST` 修改收藏夹（支持 `name/description/is_public/allow_duplicates`）
- 方法: `DELETE` 删除收藏夹

## 8. 收藏夹管理面板

- URL: `/interaction/dashboard/`
- 方法: `GET`
- 说明: 登录用户管理收藏夹的页面，同时支持模态框创建收藏夹、搜索、复制链接。

## 9. 排行榜页面

- URL: `/interaction/leaderboard/page/`
- 说明: 图形化展示排行榜，提供 `since` 查询参数筛选。

## 10. 快速收藏 API

- URL: `/interaction/quick-save/`
- 方法: `POST`
- 参数:
  - `article_id` (必填)
  - `folder` (可选，已有收藏夹 ID)
  - `folder_name` (可选，创建新收藏夹时必填)
  - `folder_description` / `folder_is_public` / `allow_duplicates` (可选)
  - `note` (可选)
- 返回：`created`、`item_id`、`folder_id`、`share_url`

## 11. 收藏夹文章列表

- URL: `/interaction/folders/<id>/items/`
- 方法: `GET`
- 说明: 返回某收藏夹下的全部条目，包含标题、链接、备注、时间。

## 12. 公开收藏夹列表

- URL: `/interaction/public/`
- 方法: `GET`
- 说明: 返回热门公开收藏夹（用于发现页）。

## 13. Swagger

- URL: `/interaction/swagger.json`
- 方法: `GET`
- 返回预测试 JSON 描述，后续可扩展 paths。

