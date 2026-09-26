## ADDED Requirements

### Requirement: 商品照片只以包裝群組管理
系統 SHALL 只提供依包裝群組（`two_pack`、`single`）列出、新增、排序商品照片的後台端點，且 MUST NOT 提供不分群組的商品層級照片端點。

#### Scenario: 呼叫已移除的商品層級列表端點
- **WHEN** 已登入管理員呼叫 `GET /api/admin/products/{id}/images`
- **THEN** 回應 404

#### Scenario: 呼叫已移除的商品層級新增端點
- **WHEN** 已登入管理員呼叫 `POST /api/admin/products/{id}/images`
- **THEN** 回應 404 或 405，資料庫不新增任何圖片

#### Scenario: 群組端點照常運作
- **WHEN** 已登入管理員呼叫 `GET /api/admin/products/{id}/images/group/two_pack`
- **THEN** 回應 200 並列出兩粒裝群組照片

#### Scenario: 刪除群組照片
- **WHEN** 已登入管理員呼叫 `DELETE /api/admin/images/{image_id}` 刪除群組照片
- **THEN** 回應 204，照片與 GCS 物件被刪除
