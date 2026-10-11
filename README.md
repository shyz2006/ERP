# ERP / MRP 系统

《电商金融》课程实验：基于 MRP 算法输出采购计划与生产计划，并提供资产负债表公式查询。

## 技术栈

- 后端框架：Django 5.2（Python Web 框架）
- 数据库：MySQL 8.0（关系型数据库），通过 PyMySQL 驱动连接
- 前端技术：HTML5 + Bootstrap 5（CDN）
- 开发环境：Windows，Python 3.13

## 功能

1. **基础数据管理**：物料表、调配构成表（BOM）、库存表的增删改查
2. **主生产计划（MPS）**：录入多条 MPS 记录（产品、数量、完工日期）
3. **MRP 计算**：
   - 需求数量 = 父物料需求数 × 构成数 ÷ (1 − 损耗率) − 工序库存 − 资材库存
   - 子物料日程完成日期 = 父物料日程下达日期
   - 子物料日程下达日期 = 完成日期 − 作业提前期 − 配料提前期 − 供应商提前期
   - 生产物料生成生产指令，采购物料生成采购指令（不做并单处理）
   - 多条 MPS 共享库存，按"日程下达日期最早"的顺序分配库存
   - 中间物料有库存时，其子物料按净需求展开
4. **资产负债公式查询**：输入一个或多个变量名，输出对应公式；支持递归展开嵌套变量

## 运行环境

- Python 3.10+，conda 环境 `kaggle_practice`（或其他装有 Django 的环境）
- MySQL 8.0，已创建数据库 `erp_db`（utf8mb4）

## 快速开始

```bat
:: 1. 安装依赖（首次）
pip install django pymysql

:: 2. 创建数据库（首次，在 MySQL 中执行）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS erp_db CHARACTER SET utf8mb4;"

:: 3. 建表并导入眼镜示例数据（首次）
python manage.py migrate
python manage.py seed_data

:: 4. 启动服务
python manage.py runserver 127.0.0.1:8010
```

浏览器访问 `http://127.0.0.1:8010/`。

> 数据库连接配置在 `erp_project/settings.py` 的 DATABASES 中
> （默认 root / 127.0.0.1:3306，密码为空）。
> 本地密码请写入 `erp_project/local_settings.py`（该文件已被 git 忽略），例如：
>
> ```python
> DATABASES = {"default": {"PASSWORD": "你的MySQL密码"}}
> ```
>
> 也可用环境变量 ERP_DB_NAME / ERP_DB_USER / ERP_DB_PASSWORD 覆盖。

## 使用流程

1. 在"物料表 / 调配构成表 / 库存表"中维护基础数据（示例数据已预置）
2. 在"主生产计划"中添加一条或多条 MPS 记录
3. 首页（或 MPS 页）点击"运行 MRP 计算"
4. 在"MRP 计算结果"查看生产计划与采购计划（按日程下达日期排序）
5. 在"资产负债公式查询"输入变量名（多个用逗号分隔）查询公式

## 测试

```bat
python manage.py test mrp
```

16 个测试覆盖：单条 MPS 手算答案对照、多订单共享库存、
中间物料有库存、公式查询（单变量/多变量/嵌套展开）。

## 项目结构

```
ERP系统/
├─ manage.py                  # Django 管理入口
├─ requirements.txt           # 依赖清单
├─ erp_project/               # 项目配置
│  ├─ settings.py             #   数据库等配置
│  └─ urls.py                 #   路由入口
└─ mrp/                       # MRP 应用
   ├─ models.py               #   物料/BOM/库存/MPS/结果/公式 模型
   ├─ services.py             #   MRP 计算引擎 + 公式查询
   ├─ views.py / urls.py      #   页面逻辑
   ├─ forms.py                #   表单
   ├─ tests.py                #   单元测试
   ├─ admin.py                #   后台管理
   ├─ management/commands/
   │  └─ seed_data.py         #   示例数据导入命令
   └─ templates/mrp/          #   Bootstrap 页面
```
