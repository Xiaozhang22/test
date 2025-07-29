# TMS运输管理系统 (Transportation Management System)

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Flask Version](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/your-repo/tms-system)

## 📋 项目简介

TMS运输管理系统是一个基于Python和Flask开发的智能物流调度管理平台，专为厂区货物调度和运输管理而设计。系统采用先进的路径规划算法和任务调度策略，实现了设备的智能调度、仓库管理、任务执行等核心功能。

### 🎯 主要特性

- **智能调度**: 基于A*算法的路径规划和优先级任务调度
- **实时监控**: 设备状态、任务进度、系统性能实时监控
- **RESTful API**: 完整的REST API接口，支持前端集成
- **数据持久化**: SQLite数据库存储，支持数据备份和恢复
- **模块化设计**: 清晰的代码结构，易于扩展和维护
- **完整日志**: 详细的操作日志和错误追踪
- **性能报告**: 系统性能分析和统计报告

### 🏗️ 系统架构

```
TMS系统架构
├── 前端展示层 (Web界面)
├── API接口层 (RESTful API)
├── 业务逻辑层 (核心算法)
├── 数据访问层 (数据库操作)
└── 基础设施层 (服务器、网络)
```

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器
- 至少 512MB 可用内存
- 至少 100MB 可用磁盘空间

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-repo/tms-system.git
cd tms-system
```

2. **创建虚拟环境**
```bash
python -m venv tms_env
source tms_env/bin/activate  # Linux/Mac
# 或
tms_env\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **初始化数据库**
```bash
python tms_system.py
```

5. **启动API服务**
```bash
python tms_api.py
```

6. **访问系统**
- API文档: http://localhost:5000
- 健康检查: http://localhost:5000/api/health
- 系统状态: http://localhost:5000/api/system/status

## 📖 使用指南

### 核心概念

#### 1. 产品 (Product)
系统中的货物实体，包含重量、体积、类别等属性。

```python
from tms_system import Product

product = Product(
    id="P001",
    name="钢材",
    weight=10.0,  # 吨
    volume=5.0,   # 立方米
    category="金属",
    unit_price=5000.0
)
```

#### 2. 仓库 (Warehouse)
存储货物的场所，分为末端库和成品库两种类型。

```python
from tms_system import TerminalWarehouse, Position

warehouse = TerminalWarehouse(
    id="TW001",
    name="末端库1",
    position=Position(0, 0),
    capacity=1000.0
)
```

#### 3. 设备 (Equipment)
执行运输任务的设备，包括行车、车头、框架等。

```python
from tms_system import Crane

crane = Crane(
    id="C001",
    name="行车1",
    position=Position(0, 1),
    warehouse_id="TW001",
    capacity=50.0
)
```

#### 4. 任务 (Task)
系统执行的工作单元，包括船运、内转、装卸等类型。

```python
from tms_system import TaskType

# 创建内转任务
task = tms_system.create_internal_transfer_task(
    source_warehouse_id="TW001",
    target_warehouse_id="PW001",
    products={"P001": 10}
)
```

### 基本操作

#### 1. 系统初始化
```python
from tms_system import TMSSystem

# 创建TMS系统实例
tms = TMSSystem(grid_size=(20, 20))

# 添加产品
tms.add_product(product)

# 添加仓库
tms.add_warehouse(warehouse)

# 添加设备
tms.add_equipment(crane)
```

#### 2. 任务管理
```python
# 创建船运任务
ship_plan = ShipPlan(
    id="SP001",
    products={"P001": 20},
    deadline=datetime.now() + timedelta(hours=4),
    priority=2
)
task = tms.create_ship_transport_task(ship_plan)

# 优化任务调度
schedule = tms.optimize_task_schedule()

# 执行任务
for task_id in schedule:
    success = tms.execute_task(task_id)
    print(f"任务 {task_id}: {'成功' if success else '失败'}")
```

#### 3. 系统监控
```python
# 获取系统状态
status = tms.get_system_status()
print(f"总设备数: {status['total_equipment']}")
print(f"活跃任务数: {status['active_tasks']}")

# 生成系统报告
report = tms.generate_report()
print(f"任务成功率: {report['performance_metrics']['task_success_rate']:.2f}%")
```

## 🔌 API接口文档

### 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **响应格式**: JSON

### 系统管理

#### 获取系统状态
```http
GET /api/system/status
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "total_products": 5,
    "total_warehouses": 4,
    "total_equipment": 8,
    "active_tasks": 2,
    "pending_tasks": 3
  }
}
```

#### 健康检查
```http
GET /api/health
```

### 产品管理

#### 获取所有产品
```http
GET /api/products
```

#### 创建产品
```http
POST /api/products
Content-Type: application/json

{
  "name": "钢材",
  "weight": 10.0,
  "volume": 5.0,
  "category": "金属",
  "unit_price": 5000.0
}
```

#### 获取单个产品
```http
GET /api/products/{product_id}
```

#### 更新产品
```http
PUT /api/products/{product_id}
Content-Type: application/json

{
  "name": "优质钢材",
  "unit_price": 5500.0
}
```

### 仓库管理

#### 获取所有仓库
```http
GET /api/warehouses
```

#### 创建仓库
```http
POST /api/warehouses
Content-Type: application/json

{
  "name": "末端库1",
  "type": "terminal",
  "position_x": 0,
  "position_y": 0,
  "capacity": 1000.0
}
```

#### 更新仓库库存
```http
POST /api/warehouses/{warehouse_id}/inventory
Content-Type: application/json

{
  "product_id": "P001",
  "quantity": 50
}
```

### 设备管理

#### 获取所有设备
```http
GET /api/equipment
```

#### 创建设备
```http
POST /api/equipment
Content-Type: application/json

{
  "name": "行车1",
  "type": "crane",
  "position_x": 0,
  "position_y": 1,
  "warehouse_id": "TW001",
  "capacity": 50.0
}
```

#### 移动设备
```http
POST /api/equipment/{equipment_id}/move
Content-Type: application/json

{
  "target_x": 5,
  "target_y": 5
}
```

### 任务管理

#### 获取所有任务
```http
GET /api/tasks
```

#### 创建船运任务
```http
POST /api/tasks/ship-transport
Content-Type: application/json

{
  "products": {"P001": 20},
  "deadline": "2024-12-31T23:59:59",
  "priority": 2,
  "ship_name": "货轮001",
  "destination": "上海港"
}
```

#### 创建内转任务
```http
POST /api/tasks/internal-transfer
Content-Type: application/json

{
  "source_warehouse_id": "TW001",
  "target_warehouse_id": "PW001",
  "products": {"P001": 10}
}
```

#### 分配设备给任务
```http
POST /api/tasks/{task_id}/assign
Content-Type: application/json

{
  "equipment_id": "C001"
}
```

#### 执行任务
```http
POST /api/tasks/{task_id}/execute
```

#### 优化任务调度
```http
POST /api/tasks/schedule/optimize
```

### 报告和统计

#### 获取系统报告
```http
GET /api/reports/system
```

#### 获取性能报告
```http
GET /api/reports/performance
```

#### 获取执行日志
```http
GET /api/logs?limit=50&offset=0
```

## 🏛️ 系统架构详解

### 核心模块

#### 1. 路径规划模块 (PathPlanner)
- **A*算法**: 实现最优路径规划
- **障碍物检测**: 动态障碍物管理
- **路径优化**: 多目标路径优化

```python
class PathPlanner:
    def a_star_path(self, start: Position, goal: Position) -> List[Position]:
        # A*算法实现
        open_set = [(0, start)]
        came_from = {}
        g_score = {(start.x, start.y): 0}
        f_score = {(start.x, start.y): self.heuristic(start, goal)}
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            if current.x == goal.x and current.y == goal.y:
                return self.reconstruct_path(came_from, current)
            # ... 算法实现
```

#### 2. 任务调度模块 (TaskScheduler)
- **优先级调度**: 基于优先级和截止时间的调度策略
- **资源分配**: 智能设备分配算法
- **冲突检测**: 任务和资源冲突检测

#### 3. 数据管理模块 (DatabaseManager)
- **SQLite支持**: 轻量级数据库存储
- **数据持久化**: 自动数据备份和恢复
- **事务管理**: 数据一致性保证

### 设计模式

#### 1. 工厂模式
用于创建不同类型的设备和仓库：

```python
class EquipmentFactory:
    @staticmethod
    def create_equipment(equipment_type: str, **kwargs) -> Equipment:
        if equipment_type == 'crane':
            return Crane(**kwargs)
        elif equipment_type == 'truck':
            return FrameTruck(**kwargs)
        # ...
```

#### 2. 观察者模式
用于设备状态变化通知：

```python
class Equipment(ABC):
    def __init__(self):
        self.observers = []
    
    def notify_observers(self, event: str):
        for observer in self.observers:
            observer.update(self, event)
```

#### 3. 策略模式
用于不同的调度策略：

```python
class SchedulingStrategy(ABC):
    @abstractmethod
    def schedule(self, tasks: List[Task]) -> List[str]:
        pass

class PrioritySchedulingStrategy(SchedulingStrategy):
    def schedule(self, tasks: List[Task]) -> List[str]:
        return sorted(tasks, key=lambda x: -x.priority)
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_tms_system.py

# 运行测试并生成覆盖率报告
pytest --cov=tms_system --cov-report=html
```

### 测试示例
```python
import pytest
from tms_system import TMSSystem, Product, Position

def test_add_product():
    tms = TMSSystem()
    product = Product("P001", "测试产品", 10.0, 5.0)
    
    assert tms.add_product(product) == True
    assert "P001" in tms.products
    assert tms.products["P001"].name == "测试产品"

def test_path_planning():
    tms = TMSSystem(grid_size=(10, 10))
    start = Position(0, 0)
    goal = Position(9, 9)
    
    path = tms.path_planner.a_star_path(start, goal)
    
    assert len(path) > 0
    assert path[0] == start
    assert path[-1] == goal
```

## 🔧 配置

### 环境变量
```bash
# .env 文件
DEBUG=True
PORT=5000
DATABASE_URL=sqlite:///tms_system.db
LOG_LEVEL=INFO
GRID_SIZE_X=20
GRID_SIZE_Y=20
```

### 配置文件
```python
# config.py
import os

class Config:
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    PORT = int(os.environ.get('PORT', 5000))
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///tms_system.db')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    GRID_SIZE = (
        int(os.environ.get('GRID_SIZE_X', 20)),
        int(os.environ.get('GRID_SIZE_Y', 20))
    )
```

## 📊 性能优化

### 1. 数据库优化
- 使用索引加速查询
- 批量操作减少I/O
- 连接池管理

### 2. 算法优化
- 路径规划缓存
- 启发式算法优化
- 并行处理

### 3. 内存管理
- 对象池模式
- 弱引用管理
- 垃圾回收优化

## 🚀 部署

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "tms_api.py"]
```

```bash
# 构建镜像
docker build -t tms-system .

# 运行容器
docker run -p 5000:5000 tms-system
```

### 生产环境部署
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 tms_api:app

# 使用nginx反向代理
sudo apt install nginx
# 配置nginx.conf
```

## 📈 监控和日志

### 日志配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tms_system.log'),
        logging.StreamHandler()
    ]
)
```

### 监控指标
- 系统响应时间
- 任务执行成功率
- 设备利用率
- 内存和CPU使用率

## 🤝 贡献指南

### 开发流程
1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范
- 遵循PEP 8编码规范
- 使用类型注解
- 编写单元测试
- 添加文档字符串

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

- 项目主页: https://github.com/your-repo/tms-system
- 问题反馈: https://github.com/your-repo/tms-system/issues
- 邮箱: tms-support@example.com

## 🙏 致谢

感谢以下开源项目的支持：
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [SQLite](https://sqlite.org/) - 数据库
- [NumPy](https://numpy.org/) - 数值计算
- [pytest](https://pytest.org/) - 测试框架

---

**TMS运输管理系统** - 让物流调度更智能、更高效！