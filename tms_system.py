"""
TMS运输管理系统核心模块
Transportation Management System Core Module

该模块包含TMS系统的核心类和算法实现
"""

import uuid
import heapq
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 枚举类定义
class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    """任务类型枚举"""
    SHIP_TRANSPORT = "ship_transport"
    INTERNAL_TRANSFER = "internal_transfer"
    LOADING = "loading"
    UNLOADING = "unloading"
    MOVE_EQUIPMENT = "move_equipment"

class EquipmentStatus(Enum):
    """设备状态枚举"""
    IDLE = "idle"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class WarehouseType(Enum):
    """仓库类型枚举"""
    TERMINAL = "terminal"
    PRODUCT = "product"
    TEMPORARY = "temporary"

# 基础数据类
@dataclass
class Position:
    """位置坐标类"""
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> float:
        """计算到另一个位置的曼哈顿距离"""
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

@dataclass
class Product:
    """产品信息类"""
    id: str
    name: str
    weight: float  # 重量(吨)
    volume: float  # 体积(立方米)
    category: str = "default"
    unit_price: float = 0.0
    
    def __post_init__(self):
        if not self.id:
            self.id = f"P{uuid.uuid4().hex[:8].upper()}"

# 基础设备类
class Equipment(ABC):
    """设备基类"""
    
    def __init__(self, id: str, name: str, position: Position):
        self.id = id or f"E{uuid.uuid4().hex[:8].upper()}"
        self.name = name
        self.position = position
        self.status = EquipmentStatus.IDLE
        self.current_task_id: Optional[str] = None
        self.last_maintenance = datetime.now()
        
    @abstractmethod
    def can_perform_task(self, task_type: TaskType) -> bool:
        """检查是否能执行指定类型的任务"""
        pass
    
    def move_to(self, target_position: Position) -> bool:
        """移动到目标位置"""
        if self.status != EquipmentStatus.IDLE:
            return False
        
        self.status = EquipmentStatus.BUSY
        # 这里应该实现实际的移动逻辑
        self.position = target_position
        self.status = EquipmentStatus.IDLE
        logger.info(f"{self.name} 移动到位置 {target_position}")
        return True

class Crane(Equipment):
    """行车类"""
    
    def __init__(self, id: str, name: str, position: Position, warehouse_id: str, capacity: float = 50.0):
        super().__init__(id, name, position)
        self.warehouse_id = warehouse_id
        self.capacity = capacity  # 起重能力(吨)
        self.current_load = 0.0
        
    def can_perform_task(self, task_type: TaskType) -> bool:
        """检查是否能执行指定类型的任务"""
        return task_type in [TaskType.LOADING, TaskType.UNLOADING, TaskType.MOVE_EQUIPMENT]
    
    def load_product(self, product: Product, quantity: int) -> bool:
        """装载产品"""
        total_weight = product.weight * quantity
        if self.current_load + total_weight > self.capacity:
            return False
        
        self.current_load += total_weight
        logger.info(f"{self.name} 装载 {quantity} 个 {product.name}")
        return True
    
    def unload_product(self, product: Product, quantity: int) -> bool:
        """卸载产品"""
        total_weight = product.weight * quantity
        if self.current_load < total_weight:
            return False
        
        self.current_load -= total_weight
        logger.info(f"{self.name} 卸载 {quantity} 个 {product.name}")
        return True

class FrameTruck(Equipment):
    """框架车头类"""
    
    def __init__(self, id: str, name: str, position: Position, capacity: float = 100.0):
        super().__init__(id, name, position)
        self.capacity = capacity
        self.attached_frame_id: Optional[str] = None
        self.current_load = 0.0
        
    def can_perform_task(self, task_type: TaskType) -> bool:
        """检查是否能执行指定类型的任务"""
        return task_type in [TaskType.SHIP_TRANSPORT, TaskType.INTERNAL_TRANSFER]
    
    def attach_frame(self, frame_id: str) -> bool:
        """连接框架"""
        if self.attached_frame_id is not None:
            return False
        
        self.attached_frame_id = frame_id
        logger.info(f"{self.name} 连接框架 {frame_id}")
        return True
    
    def detach_frame(self) -> bool:
        """分离框架"""
        if self.attached_frame_id is None:
            return False
        
        frame_id = self.attached_frame_id
        self.attached_frame_id = None
        logger.info(f"{self.name} 分离框架 {frame_id}")
        return True

class Frame(Equipment):
    """框架类"""
    
    def __init__(self, id: str, name: str, position: Position, capacity: float = 80.0):
        super().__init__(id, name, position)
        self.capacity = capacity
        self.current_load = 0.0
        self.products: Dict[str, int] = {}  # 产品ID -> 数量
        
    def can_perform_task(self, task_type: TaskType) -> bool:
        """检查是否能执行指定类型的任务"""
        return False  # 框架本身不能执行任务，需要车头牵引
    
    def load_product(self, product_id: str, quantity: int, product_weight: float) -> bool:
        """装载产品到框架"""
        total_weight = product_weight * quantity
        if self.current_load + total_weight > self.capacity:
            return False
        
        self.products[product_id] = self.products.get(product_id, 0) + quantity
        self.current_load += total_weight
        logger.info(f"框架 {self.name} 装载 {quantity} 个产品 {product_id}")
        return True
    
    def unload_product(self, product_id: str, quantity: int, product_weight: float) -> bool:
        """从框架卸载产品"""
        if product_id not in self.products or self.products[product_id] < quantity:
            return False
        
        self.products[product_id] -= quantity
        if self.products[product_id] == 0:
            del self.products[product_id]
        
        self.current_load -= product_weight * quantity
        logger.info(f"框架 {self.name} 卸载 {quantity} 个产品 {product_id}")
        return True

# 仓库类
class Warehouse(ABC):
    """仓库基类"""
    
    def __init__(self, id: str, name: str, position: Position, capacity: float, warehouse_type: WarehouseType):
        self.id = id or f"W{uuid.uuid4().hex[:8].upper()}"
        self.name = name
        self.position = position
        self.capacity = capacity
        self.warehouse_type = warehouse_type
        self.products: Dict[str, int] = {}  # 产品ID -> 数量
        self.current_volume = 0.0
        
    def add_product(self, product_id: str, quantity: int, product_volume: float = 1.0) -> bool:
        """添加产品到仓库"""
        total_volume = product_volume * quantity
        if self.current_volume + total_volume > self.capacity:
            return False
        
        self.products[product_id] = self.products.get(product_id, 0) + quantity
        self.current_volume += total_volume
        logger.info(f"仓库 {self.name} 入库 {quantity} 个产品 {product_id}")
        return True
    
    def remove_product(self, product_id: str, quantity: int, product_volume: float = 1.0) -> bool:
        """从仓库移除产品"""
        if product_id not in self.products or self.products[product_id] < quantity:
            return False
        
        self.products[product_id] -= quantity
        if self.products[product_id] == 0:
            del self.products[product_id]
        
        self.current_volume -= product_volume * quantity
        logger.info(f"仓库 {self.name} 出库 {quantity} 个产品 {product_id}")
        return True
    
    def get_available_capacity(self) -> float:
        """获取可用容量"""
        return self.capacity - self.current_volume
    
    def get_utilization_rate(self) -> float:
        """获取利用率"""
        return (self.current_volume / self.capacity) * 100 if self.capacity > 0 else 0

class TerminalWarehouse(Warehouse):
    """末端库类"""
    
    def __init__(self, id: str, name: str, position: Position, capacity: float):
        super().__init__(id, name, position, capacity, WarehouseType.TERMINAL)

class ProductWarehouse(Warehouse):
    """成品库类"""
    
    def __init__(self, id: str, name: str, position: Position, capacity: float):
        super().__init__(id, name, position, capacity, WarehouseType.PRODUCT)

# 任务相关类
@dataclass
class Task:
    """任务基类"""
    id: str
    task_type: TaskType
    priority: int = 1  # 优先级，数字越大优先级越高
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    deadline: Optional[datetime] = None
    assigned_equipment: Optional[str] = None
    sub_tasks: List['Task'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"T{uuid.uuid4().hex[:8].upper()}"
    
    def add_sub_task(self, sub_task: 'Task'):
        """添加子任务"""
        self.sub_tasks.append(sub_task)
    
    def start_execution(self):
        """开始执行任务"""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = datetime.now()
        logger.info(f"任务 {self.id} 开始执行")
    
    def complete_task(self):
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.end_time = datetime.now()
        logger.info(f"任务 {self.id} 执行完成")
    
    def fail_task(self, reason: str = ""):
        """任务失败"""
        self.status = TaskStatus.FAILED
        self.end_time = datetime.now()
        self.metadata['failure_reason'] = reason
        logger.error(f"任务 {self.id} 执行失败: {reason}")

@dataclass
class ShipPlan:
    """船运计划类"""
    id: str
    products: Dict[str, int]  # 产品ID -> 数量
    deadline: datetime
    priority: int = 1
    ship_name: str = ""
    destination: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"SP{uuid.uuid4().hex[:8].upper()}"

# 路径规划算法
class PathPlanner:
    """路径规划器"""
    
    def __init__(self, grid_size: Tuple[int, int]):
        self.grid_width, self.grid_height = grid_size
        self.obstacles: set = set()
        
    def add_obstacle(self, position: Position):
        """添加障碍物"""
        self.obstacles.add((position.x, position.y))
    
    def remove_obstacle(self, position: Position):
        """移除障碍物"""
        self.obstacles.discard((position.x, position.y))
    
    def heuristic(self, pos1: Position, pos2: Position) -> float:
        """启发式函数（曼哈顿距离）"""
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)
    
    def get_neighbors(self, position: Position) -> List[Position]:
        """获取相邻位置"""
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 上右下左
        
        for dx, dy in directions:
            new_x, new_y = position.x + dx, position.y + dy
            if (0 <= new_x < self.grid_width and 
                0 <= new_y < self.grid_height and 
                (new_x, new_y) not in self.obstacles):
                neighbors.append(Position(new_x, new_y))
        
        return neighbors
    
    def a_star_path(self, start: Position, goal: Position) -> List[Position]:
        """A*路径规划算法"""
        if (start.x, start.y) in self.obstacles or (goal.x, goal.y) in self.obstacles:
            return []
        
        open_set = [(0, start)]
        came_from: Dict[Tuple[int, int], Position] = {}
        g_score = {(start.x, start.y): 0}
        f_score = {(start.x, start.y): self.heuristic(start, goal)}
        
        while open_set:
            current_f, current = heapq.heappop(open_set)
            
            if current.x == goal.x and current.y == goal.y:
                # 重构路径
                path = []
                current_pos = current
                while (current_pos.x, current_pos.y) in came_from:
                    path.append(current_pos)
                    current_pos = came_from[(current_pos.x, current_pos.y)]
                path.append(start)
                path.reverse()
                return path
            
            for neighbor in self.get_neighbors(current):
                tentative_g_score = g_score[(current.x, current.y)] + 1
                neighbor_key = (neighbor.x, neighbor.y)
                
                if neighbor_key not in g_score or tentative_g_score < g_score[neighbor_key]:
                    came_from[neighbor_key] = current
                    g_score[neighbor_key] = tentative_g_score
                    f_score[neighbor_key] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor_key], neighbor))
        
        return []  # 无法找到路径

# 数据库管理
class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "tms_system.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 产品表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    weight REAL,
                    volume REAL,
                    category TEXT DEFAULT 'default',
                    unit_price REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 仓库表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warehouses (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    position_x INTEGER,
                    position_y INTEGER,
                    capacity REAL,
                    current_volume REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 设备表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS equipment (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    position_x INTEGER,
                    position_y INTEGER,
                    status TEXT DEFAULT 'idle',
                    capacity REAL,
                    warehouse_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    deadline TIMESTAMP,
                    assigned_equipment TEXT,
                    metadata TEXT
                )
            ''')
            
            # 库存表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    warehouse_id TEXT,
                    product_id TEXT,
                    quantity INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (warehouse_id, product_id)
                )
            ''')
            
            conn.commit()
    
    def save_product(self, product: Product):
        """保存产品信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO products 
                (id, name, weight, volume, category, unit_price)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (product.id, product.name, product.weight, product.volume, 
                  product.category, product.unit_price))
            conn.commit()
    
    def save_warehouse(self, warehouse: Warehouse):
        """保存仓库信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO warehouses 
                (id, name, type, position_x, position_y, capacity, current_volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (warehouse.id, warehouse.name, warehouse.warehouse_type.value,
                  warehouse.position.x, warehouse.position.y, 
                  warehouse.capacity, warehouse.current_volume))
            conn.commit()
    
    def save_task(self, task: Task):
        """保存任务信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, type, status, priority, created_at, start_time, end_time, 
                 deadline, assigned_equipment, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task.id, task.task_type.value, task.status.value, task.priority,
                  task.created_at, task.start_time, task.end_time, task.deadline,
                  task.assigned_equipment, json.dumps(task.metadata)))
            conn.commit()

# 主系统类
class TMSSystem:
    """TMS运输管理系统主类"""
    
    def __init__(self, grid_size: Tuple[int, int] = (20, 20), db_path: str = "tms_system.db"):
        self.grid_size = grid_size
        self.path_planner = PathPlanner(grid_size)
        self.db_manager = DatabaseManager(db_path)
        
        # 系统组件
        self.products: Dict[str, Product] = {}
        self.warehouses: Dict[str, Warehouse] = {}
        self.equipment: Dict[str, Equipment] = {}
        self.tasks: Dict[str, Task] = {}
        self.ship_plans: Dict[str, ShipPlan] = {}
        
        # 执行日志
        self.execution_log: List[str] = []
        
        logger.info("TMS系统初始化完成")
    
    def add_product(self, product: Product) -> bool:
        """添加产品"""
        try:
            self.products[product.id] = product
            self.db_manager.save_product(product)
            logger.info(f"添加产品: {product.name}")
            return True
        except Exception as e:
            logger.error(f"添加产品失败: {e}")
            return False
    
    def add_warehouse(self, warehouse: Warehouse) -> bool:
        """添加仓库"""
        try:
            self.warehouses[warehouse.id] = warehouse
            self.db_manager.save_warehouse(warehouse)
            logger.info(f"添加仓库: {warehouse.name}")
            return True
        except Exception as e:
            logger.error(f"添加仓库失败: {e}")
            return False
    
    def add_equipment(self, equipment: Equipment) -> bool:
        """添加设备"""
        try:
            self.equipment[equipment.id] = equipment
            # 将设备位置添加为临时障碍物
            self.path_planner.add_obstacle(equipment.position)
            logger.info(f"添加设备: {equipment.name}")
            return True
        except Exception as e:
            logger.error(f"添加设备失败: {e}")
            return False
    
    def create_ship_transport_task(self, ship_plan: ShipPlan) -> Optional[Task]:
        """创建船运任务"""
        try:
            task = Task(
                id="",
                task_type=TaskType.SHIP_TRANSPORT,
                priority=ship_plan.priority,
                deadline=ship_plan.deadline,
                metadata={
                    'ship_plan_id': ship_plan.id,
                    'products': ship_plan.products,
                    'ship_name': ship_plan.ship_name,
                    'destination': ship_plan.destination
                }
            )
            
            # 创建子任务
            for product_id, quantity in ship_plan.products.items():
                # 装载任务
                loading_task = Task(
                    id="",
                    task_type=TaskType.LOADING,
                    metadata={'product_id': product_id, 'quantity': quantity}
                )
                task.add_sub_task(loading_task)
                
                # 运输任务
                transport_task = Task(
                    id="",
                    task_type=TaskType.SHIP_TRANSPORT,
                    metadata={'product_id': product_id, 'quantity': quantity}
                )
                task.add_sub_task(transport_task)
            
            self.tasks[task.id] = task
            self.db_manager.save_task(task)
            logger.info(f"创建船运任务: {task.id}")
            return task
            
        except Exception as e:
            logger.error(f"创建船运任务失败: {e}")
            return None
    
    def create_internal_transfer_task(self, source_warehouse_id: str, 
                                    target_warehouse_id: str, 
                                    products: Dict[str, int]) -> Optional[Task]:
        """创建内转任务"""
        try:
            task = Task(
                id="",
                task_type=TaskType.INTERNAL_TRANSFER,
                metadata={
                    'source_warehouse_id': source_warehouse_id,
                    'target_warehouse_id': target_warehouse_id,
                    'products': products
                }
            )
            
            self.tasks[task.id] = task
            self.db_manager.save_task(task)
            logger.info(f"创建内转任务: {task.id}")
            return task
            
        except Exception as e:
            logger.error(f"创建内转任务失败: {e}")
            return None
    
    def assign_equipment_to_task(self, task_id: str, equipment_id: str) -> bool:
        """为任务分配设备"""
        if task_id not in self.tasks or equipment_id not in self.equipment:
            return False
        
        task = self.tasks[task_id]
        equipment = self.equipment[equipment_id]
        
        if not equipment.can_perform_task(task.task_type):
            return False
        
        if equipment.status != EquipmentStatus.IDLE:
            return False
        
        task.assigned_equipment = equipment_id
        equipment.current_task_id = task_id
        equipment.status = EquipmentStatus.BUSY
        
        logger.info(f"设备 {equipment.name} 分配给任务 {task.id}")
        return True
    
    def execute_task(self, task_id: str) -> bool:
        """执行任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        try:
            task.start_execution()
            
            # 根据任务类型执行相应逻辑
            if task.task_type == TaskType.SHIP_TRANSPORT:
                self._execute_ship_transport_task(task)
            elif task.task_type == TaskType.INTERNAL_TRANSFER:
                self._execute_internal_transfer_task(task)
            elif task.task_type == TaskType.LOADING:
                self._execute_loading_task(task)
            elif task.task_type == TaskType.UNLOADING:
                self._execute_unloading_task(task)
            
            task.complete_task()
            
            # 释放设备
            if task.assigned_equipment:
                equipment = self.equipment[task.assigned_equipment]
                equipment.status = EquipmentStatus.IDLE
                equipment.current_task_id = None
            
            self.db_manager.save_task(task)
            return True
            
        except Exception as e:
            task.fail_task(str(e))
            logger.error(f"任务执行失败: {e}")
            return False
    
    def _execute_ship_transport_task(self, task: Task):
        """执行船运任务"""
        products = task.metadata.get('products', {})
        
        for product_id, quantity in products.items():
            # 从成品库取货
            product_warehouses = [w for w in self.warehouses.values() 
                                if isinstance(w, ProductWarehouse)]
            
            for warehouse in product_warehouses:
                if product_id in warehouse.products and warehouse.products[product_id] >= quantity:
                    product = self.products[product_id]
                    warehouse.remove_product(product_id, quantity, product.volume)
                    self.execution_log.append(f"从 {warehouse.name} 取出 {quantity} 个 {product.name}")
                    break
    
    def _execute_internal_transfer_task(self, task: Task):
        """执行内转任务"""
        source_id = task.metadata['source_warehouse_id']
        target_id = task.metadata['target_warehouse_id']
        products = task.metadata['products']
        
        source_warehouse = self.warehouses[source_id]
        target_warehouse = self.warehouses[target_id]
        
        for product_id, quantity in products.items():
            if (product_id in source_warehouse.products and 
                source_warehouse.products[product_id] >= quantity):
                
                product = self.products[product_id]
                
                # 从源仓库移除
                source_warehouse.remove_product(product_id, quantity, product.volume)
                
                # 添加到目标仓库
                target_warehouse.add_product(product_id, quantity, product.volume)
                
                self.execution_log.append(
                    f"从 {source_warehouse.name} 转移 {quantity} 个 {product.name} "
                    f"到 {target_warehouse.name}"
                )
    
    def _execute_loading_task(self, task: Task):
        """执行装载任务"""
        product_id = task.metadata['product_id']
        quantity = task.metadata['quantity']
        
        # 查找可用的行车
        available_cranes = [eq for eq in self.equipment.values() 
                           if isinstance(eq, Crane) and eq.status == EquipmentStatus.IDLE]
        
        if available_cranes:
            crane = available_cranes[0]
            product = self.products[product_id]
            crane.load_product(product, quantity)
            self.execution_log.append(f"{crane.name} 装载 {quantity} 个 {product.name}")
    
    def _execute_unloading_task(self, task: Task):
        """执行卸载任务"""
        product_id = task.metadata['product_id']
        quantity = task.metadata['quantity']
        
        # 查找正在装载该产品的行车
        loaded_cranes = [eq for eq in self.equipment.values() 
                        if isinstance(eq, Crane) and eq.current_load > 0]
        
        if loaded_cranes:
            crane = loaded_cranes[0]
            product = self.products[product_id]
            crane.unload_product(product, quantity)
            self.execution_log.append(f"{crane.name} 卸载 {quantity} 个 {product.name}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'total_products': len(self.products),
            'total_warehouses': len(self.warehouses),
            'total_equipment': len(self.equipment),
            'active_tasks': len([t for t in self.tasks.values() 
                               if t.status == TaskStatus.IN_PROGRESS]),
            'pending_tasks': len([t for t in self.tasks.values() 
                                if t.status == TaskStatus.PENDING]),
            'equipment_status': {
                'idle': len([e for e in self.equipment.values() 
                           if e.status == EquipmentStatus.IDLE]),
                'busy': len([e for e in self.equipment.values() 
                           if e.status == EquipmentStatus.BUSY]),
                'maintenance': len([e for e in self.equipment.values() 
                                 if e.status == EquipmentStatus.MAINTENANCE])
            },
            'warehouse_utilization': {
                wh.id: wh.get_utilization_rate() 
                for wh in self.warehouses.values()
            }
        }
    
    def optimize_task_schedule(self) -> List[str]:
        """优化任务调度"""
        pending_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        
        # 按优先级和截止时间排序
        sorted_tasks = sorted(
            pending_tasks, 
            key=lambda x: (-x.priority, x.deadline or datetime.max)
        )
        
        optimized_schedule = []
        for task in sorted_tasks:
            # 为任务分配最合适的设备
            suitable_equipment = [
                eq for eq in self.equipment.values()
                if eq.can_perform_task(task.task_type) and eq.status == EquipmentStatus.IDLE
            ]
            
            if suitable_equipment:
                # 选择距离最近的设备
                best_equipment = min(
                    suitable_equipment,
                    key=lambda eq: self._calculate_task_equipment_distance(task, eq)
                )
                
                if self.assign_equipment_to_task(task.id, best_equipment.id):
                    optimized_schedule.append(task.id)
        
        return optimized_schedule
    
    def _calculate_task_equipment_distance(self, task: Task, equipment: Equipment) -> float:
        """计算任务与设备的距离（用于设备选择）"""
        # 简化实现，实际应根据任务类型和位置计算
        if 'source_warehouse_id' in task.metadata:
            source_warehouse = self.warehouses[task.metadata['source_warehouse_id']]
            return equipment.position.distance_to(source_warehouse.position)
        return 0.0
    
    def generate_report(self) -> Dict[str, Any]:
        """生成系统报告"""
        completed_tasks = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        
        total_execution_time = sum([
            (t.end_time - t.start_time).total_seconds() 
            for t in completed_tasks if t.start_time and t.end_time
        ])
        
        return {
            'system_overview': self.get_system_status(),
            'performance_metrics': {
                'total_completed_tasks': len(completed_tasks),
                'average_execution_time': total_execution_time / len(completed_tasks) if completed_tasks else 0,
                'task_success_rate': len(completed_tasks) / len(self.tasks) * 100 if self.tasks else 0
            },
            'resource_utilization': {
                'warehouse_utilization': {
                    wh.id: {
                        'name': wh.name,
                        'utilization_rate': wh.get_utilization_rate(),
                        'available_capacity': wh.get_available_capacity()
                    }
                    for wh in self.warehouses.values()
                },
                'equipment_status': {
                    eq.id: {
                        'name': eq.name,
                        'status': eq.status.value,
                        'current_task': eq.current_task_id
                    }
                    for eq in self.equipment.values()
                }
            },
            'recent_logs': self.execution_log[-20:]  # 最近20条日志
        }

# 示例使用
if __name__ == "__main__":
    # 创建TMS系统实例
    tms = TMSSystem()
    
    # 添加产品
    products = [
        Product("P001", "钢材", 10.0, 5.0, "金属", 5000.0),
        Product("P002", "水泥", 8.0, 4.0, "建材", 800.0),
        Product("P003", "木材", 5.0, 8.0, "建材", 1200.0)
    ]
    
    for product in products:
        tms.add_product(product)
    
    # 添加仓库
    terminal_wh = TerminalWarehouse("TW001", "末端库1", Position(0, 0), 1000.0)
    product_wh = ProductWarehouse("PW001", "成品库1", Position(10, 10), 2000.0)
    
    tms.add_warehouse(terminal_wh)
    tms.add_warehouse(product_wh)
    
    # 添加设备
    crane1 = Crane("C001", "行车1", Position(0, 1), "TW001", 50.0)
    crane2 = Crane("C002", "行车2", Position(10, 11), "PW001", 50.0)
    truck1 = FrameTruck("T001", "车头1", Position(5, 5), 100.0)
    frame1 = Frame("F001", "框架1", Position(5, 6), 80.0)
    
    tms.add_equipment(crane1)
    tms.add_equipment(crane2)
    tms.add_equipment(truck1)
    tms.add_equipment(frame1)
    
    # 添加库存
    terminal_wh.add_product("P001", 100, 5.0)
    terminal_wh.add_product("P002", 80, 4.0)
    product_wh.add_product("P003", 50, 8.0)
    
    # 创建船运计划
    ship_plan = ShipPlan(
        "SP001",
        {"P003": 20},
        datetime.now() + timedelta(hours=4),
        priority=2,
        ship_name="货轮001",
        destination="上海港"
    )
    
    tms.ship_plans[ship_plan.id] = ship_plan
    
    # 创建任务
    ship_task = tms.create_ship_transport_task(ship_plan)
    transfer_task = tms.create_internal_transfer_task("TW001", "PW001", {"P001": 10})
    
    # 优化调度
    schedule = tms.optimize_task_schedule()
    print(f"优化后的任务调度: {schedule}")
    
    # 执行任务
    for task_id in schedule:
        success = tms.execute_task(task_id)
        print(f"任务 {task_id} 执行结果: {'成功' if success else '失败'}")
    
    # 生成报告
    report = tms.generate_report()
    print(f"\n系统报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))