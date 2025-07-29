"""
TMS运输管理系统API接口
Transportation Management System REST API

该模块提供完整的RESTful API接口，用于TMS系统的Web服务
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
import logging
from typing import Dict, Any

from tms_system import (
    TMSSystem, Product, TerminalWarehouse, ProductWarehouse, 
    Crane, FrameTruck, Frame, Position, ShipPlan,
    TaskStatus, TaskType, EquipmentStatus, WarehouseType
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 全局TMS系统实例
tms_system = TMSSystem()

# 错误处理装饰器
def handle_api_errors(f):
    """API错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API错误: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'message': '服务器内部错误'
            }), 500
    wrapper.__name__ = f.__name__
    return wrapper

# 数据验证函数
def validate_required_fields(data: Dict, required_fields: list) -> tuple:
    """验证必需字段"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return False, f"缺少必需字段: {', '.join(missing_fields)}"
    return True, ""

def validate_position(data: Dict) -> tuple:
    """验证位置数据"""
    try:
        x = int(data.get('position_x', 0))
        y = int(data.get('position_y', 0))
        if x < 0 or y < 0 or x >= tms_system.grid_size[0] or y >= tms_system.grid_size[1]:
            return False, f"位置坐标超出范围 (0-{tms_system.grid_size[0]-1}, 0-{tms_system.grid_size[1]-1})"
        return True, ""
    except (ValueError, TypeError):
        return False, "位置坐标必须为有效整数"

# 首页和文档路由
@app.route('/')
def index():
    """系统首页"""
    return jsonify({
        'message': 'TMS运输管理系统API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'system': '/api/system',
            'products': '/api/products',
            'warehouses': '/api/warehouses',
            'equipment': '/api/equipment',
            'tasks': '/api/tasks',
            'reports': '/api/reports'
        }
    })

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'system_status': tms_system.get_system_status()
    })

# 系统管理API
@app.route('/api/system/status')
@handle_api_errors
def get_system_status():
    """获取系统状态"""
    return jsonify({
        'success': True,
        'data': tms_system.get_system_status()
    })

@app.route('/api/system/reset', methods=['POST'])
@handle_api_errors
def reset_system():
    """重置系统"""
    global tms_system
    tms_system = TMSSystem()
    logger.info("系统已重置")
    return jsonify({
        'success': True,
        'message': '系统重置成功'
    })

# 产品管理API
@app.route('/api/products', methods=['GET'])
@handle_api_errors
def get_products():
    """获取所有产品"""
    products_data = {}
    for product_id, product in tms_system.products.items():
        products_data[product_id] = {
            'id': product.id,
            'name': product.name,
            'weight': product.weight,
            'volume': product.volume,
            'category': product.category,
            'unit_price': product.unit_price
        }
    
    return jsonify({
        'success': True,
        'data': products_data,
        'count': len(products_data)
    })

@app.route('/api/products', methods=['POST'])
@handle_api_errors
def create_product():
    """创建产品"""
    data = request.get_json()
    
    # 验证必需字段
    required_fields = ['name', 'weight', 'volume']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        product = Product(
            id=data.get('id', ''),
            name=data['name'],
            weight=float(data['weight']),
            volume=float(data['volume']),
            category=data.get('category', 'default'),
            unit_price=float(data.get('unit_price', 0.0))
        )
        
        success = tms_system.add_product(product)
        if success:
            return jsonify({
                'success': True,
                'message': '产品创建成功',
                'data': {'id': product.id, 'name': product.name}
            })
        else:
            return jsonify({'success': False, 'message': '产品创建失败'}), 500
            
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'数据类型错误: {str(e)}'}), 400

@app.route('/api/products/<product_id>', methods=['GET'])
@handle_api_errors
def get_product(product_id):
    """获取单个产品信息"""
    if product_id not in tms_system.products:
        return jsonify({'success': False, 'message': '产品不存在'}), 404
    
    product = tms_system.products[product_id]
    return jsonify({
        'success': True,
        'data': {
            'id': product.id,
            'name': product.name,
            'weight': product.weight,
            'volume': product.volume,
            'category': product.category,
            'unit_price': product.unit_price
        }
    })

@app.route('/api/products/<product_id>', methods=['PUT'])
@handle_api_errors
def update_product(product_id):
    """更新产品信息"""
    if product_id not in tms_system.products:
        return jsonify({'success': False, 'message': '产品不存在'}), 404
    
    data = request.get_json()
    product = tms_system.products[product_id]
    
    # 更新字段
    if 'name' in data:
        product.name = data['name']
    if 'weight' in data:
        product.weight = float(data['weight'])
    if 'volume' in data:
        product.volume = float(data['volume'])
    if 'category' in data:
        product.category = data['category']
    if 'unit_price' in data:
        product.unit_price = float(data['unit_price'])
    
    # 保存到数据库
    tms_system.db_manager.save_product(product)
    
    return jsonify({
        'success': True,
        'message': '产品更新成功',
        'data': {'id': product.id, 'name': product.name}
    })

# 仓库管理API
@app.route('/api/warehouses', methods=['GET'])
@handle_api_errors
def get_warehouses():
    """获取所有仓库"""
    warehouses_data = {}
    for warehouse_id, warehouse in tms_system.warehouses.items():
        warehouses_data[warehouse_id] = {
            'id': warehouse.id,
            'name': warehouse.name,
            'type': warehouse.warehouse_type.value,
            'position': {'x': warehouse.position.x, 'y': warehouse.position.y},
            'capacity': warehouse.capacity,
            'current_volume': warehouse.current_volume,
            'utilization_rate': warehouse.get_utilization_rate(),
            'available_capacity': warehouse.get_available_capacity(),
            'products': warehouse.products
        }
    
    return jsonify({
        'success': True,
        'data': warehouses_data,
        'count': len(warehouses_data)
    })

@app.route('/api/warehouses', methods=['POST'])
@handle_api_errors
def create_warehouse():
    """创建仓库"""
    data = request.get_json()
    
    # 验证必需字段
    required_fields = ['name', 'type', 'position_x', 'position_y', 'capacity']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # 验证位置
    is_valid, error_msg = validate_position(data)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        warehouse_type = data['type'].lower()
        position = Position(int(data['position_x']), int(data['position_y']))
        capacity = float(data['capacity'])
        
        if warehouse_type == 'terminal':
            warehouse = TerminalWarehouse(
                id=data.get('id', ''),
                name=data['name'],
                position=position,
                capacity=capacity
            )
        elif warehouse_type == 'product':
            warehouse = ProductWarehouse(
                id=data.get('id', ''),
                name=data['name'],
                position=position,
                capacity=capacity
            )
        else:
            return jsonify({'success': False, 'message': '仓库类型必须为 terminal 或 product'}), 400
        
        success = tms_system.add_warehouse(warehouse)
        if success:
            return jsonify({
                'success': True,
                'message': '仓库创建成功',
                'data': {'id': warehouse.id, 'name': warehouse.name}
            })
        else:
            return jsonify({'success': False, 'message': '仓库创建失败'}), 500
            
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'数据类型错误: {str(e)}'}), 400

@app.route('/api/warehouses/<warehouse_id>/inventory', methods=['POST'])
@handle_api_errors
def update_warehouse_inventory():
    """更新仓库库存"""
    warehouse_id = request.view_args['warehouse_id']
    data = request.get_json()
    
    if warehouse_id not in tms_system.warehouses:
        return jsonify({'success': False, 'message': '仓库不存在'}), 404
    
    required_fields = ['product_id', 'quantity']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    warehouse = tms_system.warehouses[warehouse_id]
    product_id = data['product_id']
    quantity = int(data['quantity'])
    
    if product_id not in tms_system.products:
        return jsonify({'success': False, 'message': '产品不存在'}), 404
    
    product = tms_system.products[product_id]
    
    try:
        if quantity > 0:
            success = warehouse.add_product(product_id, quantity, product.volume)
            operation = '入库'
        else:
            success = warehouse.remove_product(product_id, abs(quantity), product.volume)
            operation = '出库'
        
        if success:
            return jsonify({
                'success': True,
                'message': f'库存{operation}成功',
                'data': {
                    'warehouse_id': warehouse_id,
                    'product_id': product_id,
                    'quantity': quantity,
                    'current_stock': warehouse.products.get(product_id, 0)
                }
            })
        else:
            return jsonify({'success': False, 'message': f'库存{operation}失败'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'}), 500

# 设备管理API
@app.route('/api/equipment', methods=['GET'])
@handle_api_errors
def get_equipment():
    """获取所有设备"""
    equipment_data = {}
    for equipment_id, equipment in tms_system.equipment.items():
        equipment_info = {
            'id': equipment.id,
            'name': equipment.name,
            'type': equipment.__class__.__name__,
            'position': {'x': equipment.position.x, 'y': equipment.position.y},
            'status': equipment.status.value,
            'current_task_id': equipment.current_task_id
        }
        
        # 添加特定设备类型的信息
        if isinstance(equipment, Crane):
            equipment_info.update({
                'warehouse_id': equipment.warehouse_id,
                'capacity': equipment.capacity,
                'current_load': equipment.current_load
            })
        elif isinstance(equipment, FrameTruck):
            equipment_info.update({
                'capacity': equipment.capacity,
                'attached_frame_id': equipment.attached_frame_id,
                'current_load': equipment.current_load
            })
        elif isinstance(equipment, Frame):
            equipment_info.update({
                'capacity': equipment.capacity,
                'current_load': equipment.current_load,
                'products': equipment.products
            })
        
        equipment_data[equipment_id] = equipment_info
    
    return jsonify({
        'success': True,
        'data': equipment_data,
        'count': len(equipment_data)
    })

@app.route('/api/equipment', methods=['POST'])
@handle_api_errors
def create_equipment():
    """创建设备"""
    data = request.get_json()
    
    # 验证必需字段
    required_fields = ['name', 'type', 'position_x', 'position_y']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # 验证位置
    is_valid, error_msg = validate_position(data)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        equipment_type = data['type'].lower()
        position = Position(int(data['position_x']), int(data['position_y']))
        
        if equipment_type == 'crane':
            if 'warehouse_id' not in data:
                return jsonify({'success': False, 'message': '行车必须指定所属仓库'}), 400
            
            equipment = Crane(
                id=data.get('id', ''),
                name=data['name'],
                position=position,
                warehouse_id=data['warehouse_id'],
                capacity=float(data.get('capacity', 50.0))
            )
        elif equipment_type == 'frametruck':
            equipment = FrameTruck(
                id=data.get('id', ''),
                name=data['name'],
                position=position,
                capacity=float(data.get('capacity', 100.0))
            )
        elif equipment_type == 'frame':
            equipment = Frame(
                id=data.get('id', ''),
                name=data['name'],
                position=position,
                capacity=float(data.get('capacity', 80.0))
            )
        else:
            return jsonify({'success': False, 'message': '设备类型必须为 crane, frametruck 或 frame'}), 400
        
        success = tms_system.add_equipment(equipment)
        if success:
            return jsonify({
                'success': True,
                'message': '设备创建成功',
                'data': {'id': equipment.id, 'name': equipment.name}
            })
        else:
            return jsonify({'success': False, 'message': '设备创建失败'}), 500
            
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'数据类型错误: {str(e)}'}), 400

@app.route('/api/equipment/<equipment_id>/move', methods=['POST'])
@handle_api_errors
def move_equipment(equipment_id):
    """移动设备"""
    data = request.get_json()
    
    if equipment_id not in tms_system.equipment:
        return jsonify({'success': False, 'message': '设备不存在'}), 404
    
    required_fields = ['target_x', 'target_y']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        target_position = Position(int(data['target_x']), int(data['target_y']))
        equipment = tms_system.equipment[equipment_id]
        
        # 使用路径规划算法计算路径
        path = tms_system.path_planner.a_star_path(equipment.position, target_position)
        
        if not path:
            return jsonify({'success': False, 'message': '无法找到有效路径'}), 400
        
        # 移动设备
        success = equipment.move_to(target_position)
        
        if success:
            return jsonify({
                'success': True,
                'message': '设备移动成功',
                'data': {
                    'equipment_id': equipment_id,
                    'old_position': {'x': path[0].x, 'y': path[0].y},
                    'new_position': {'x': target_position.x, 'y': target_position.y},
                    'path': [{'x': pos.x, 'y': pos.y} for pos in path]
                }
            })
        else:
            return jsonify({'success': False, 'message': '设备移动失败'}), 400
            
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'坐标数据错误: {str(e)}'}), 400

# 任务管理API
@app.route('/api/tasks', methods=['GET'])
@handle_api_errors
def get_tasks():
    """获取所有任务"""
    tasks_data = {}
    for task_id, task in tms_system.tasks.items():
        tasks_data[task_id] = {
            'id': task.id,
            'type': task.task_type.value,
            'status': task.status.value,
            'priority': task.priority,
            'created_at': task.created_at.isoformat(),
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'assigned_equipment': task.assigned_equipment,
            'metadata': task.metadata,
            'sub_tasks': [
                {
                    'id': st.id,
                    'type': st.task_type.value,
                    'status': st.status.value
                } for st in task.sub_tasks
            ]
        }
    
    return jsonify({
        'success': True,
        'data': tasks_data,
        'count': len(tasks_data)
    })

@app.route('/api/tasks/ship-transport', methods=['POST'])
@handle_api_errors
def create_ship_transport_task():
    """创建船运任务"""
    data = request.get_json()
    
    required_fields = ['products', 'deadline']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        # 解析截止时间
        deadline = datetime.fromisoformat(data['deadline'].replace('Z', '+00:00'))
        
        # 创建船运计划
        ship_plan = ShipPlan(
            id=data.get('plan_id', ''),
            products=data['products'],
            deadline=deadline,
            priority=int(data.get('priority', 1)),
            ship_name=data.get('ship_name', ''),
            destination=data.get('destination', '')
        )
        
        tms_system.ship_plans[ship_plan.id] = ship_plan
        
        # 创建船运任务
        task = tms_system.create_ship_transport_task(ship_plan)
        
        if task:
            return jsonify({
                'success': True,
                'message': '船运任务创建成功',
                'data': {
                    'task_id': task.id,
                    'plan_id': ship_plan.id,
                    'deadline': deadline.isoformat()
                }
            })
        else:
            return jsonify({'success': False, 'message': '船运任务创建失败'}), 500
            
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'message': f'数据格式错误: {str(e)}'}), 400

@app.route('/api/tasks/internal-transfer', methods=['POST'])
@handle_api_errors
def create_internal_transfer_task():
    """创建内转任务"""
    data = request.get_json()
    
    required_fields = ['source_warehouse_id', 'target_warehouse_id', 'products']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # 验证仓库是否存在
    if data['source_warehouse_id'] not in tms_system.warehouses:
        return jsonify({'success': False, 'message': '源仓库不存在'}), 404
    
    if data['target_warehouse_id'] not in tms_system.warehouses:
        return jsonify({'success': False, 'message': '目标仓库不存在'}), 404
    
    try:
        task = tms_system.create_internal_transfer_task(
            data['source_warehouse_id'],
            data['target_warehouse_id'],
            data['products']
        )
        
        if task:
            return jsonify({
                'success': True,
                'message': '内转任务创建成功',
                'data': {'task_id': task.id}
            })
        else:
            return jsonify({'success': False, 'message': '内转任务创建失败'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'任务创建失败: {str(e)}'}), 500

@app.route('/api/tasks/<task_id>/assign', methods=['POST'])
@handle_api_errors
def assign_task_equipment(task_id):
    """为任务分配设备"""
    data = request.get_json()
    
    if task_id not in tms_system.tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    required_fields = ['equipment_id']
    is_valid, error_msg = validate_required_fields(data, required_fields)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    equipment_id = data['equipment_id']
    if equipment_id not in tms_system.equipment:
        return jsonify({'success': False, 'message': '设备不存在'}), 404
    
    success = tms_system.assign_equipment_to_task(task_id, equipment_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': '设备分配成功',
            'data': {
                'task_id': task_id,
                'equipment_id': equipment_id
            }
        })
    else:
        return jsonify({'success': False, 'message': '设备分配失败'}), 400

@app.route('/api/tasks/<task_id>/execute', methods=['POST'])
@handle_api_errors
def execute_task(task_id):
    """执行任务"""
    if task_id not in tms_system.tasks:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    success = tms_system.execute_task(task_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': '任务执行成功',
            'data': {
                'task_id': task_id,
                'execution_logs': tms_system.execution_log[-5:]  # 最近5条日志
            }
        })
    else:
        return jsonify({'success': False, 'message': '任务执行失败'}), 400

@app.route('/api/tasks/schedule/optimize', methods=['POST'])
@handle_api_errors
def optimize_task_schedule():
    """优化任务调度"""
    schedule = tms_system.optimize_task_schedule()
    
    return jsonify({
        'success': True,
        'message': '任务调度优化完成',
        'data': {
            'optimized_schedule': schedule,
            'total_tasks': len(schedule)
        }
    })

# 报告和统计API
@app.route('/api/reports/system', methods=['GET'])
@handle_api_errors
def get_system_report():
    """获取系统报告"""
    report = tms_system.generate_report()
    
    return jsonify({
        'success': True,
        'data': report,
        'generated_at': datetime.now().isoformat()
    })

@app.route('/api/reports/performance', methods=['GET'])
@handle_api_errors
def get_performance_report():
    """获取性能报告"""
    completed_tasks = [t for t in tms_system.tasks.values() if t.status == TaskStatus.COMPLETED]
    failed_tasks = [t for t in tms_system.tasks.values() if t.status == TaskStatus.FAILED]
    
    # 计算平均执行时间
    total_execution_time = 0
    for task in completed_tasks:
        if task.start_time and task.end_time:
            total_execution_time += (task.end_time - task.start_time).total_seconds()
    
    avg_execution_time = total_execution_time / len(completed_tasks) if completed_tasks else 0
    
    # 按任务类型统计
    task_type_stats = {}
    for task in tms_system.tasks.values():
        task_type = task.task_type.value
        if task_type not in task_type_stats:
            task_type_stats[task_type] = {'total': 0, 'completed': 0, 'failed': 0}
        
        task_type_stats[task_type]['total'] += 1
        if task.status == TaskStatus.COMPLETED:
            task_type_stats[task_type]['completed'] += 1
        elif task.status == TaskStatus.FAILED:
            task_type_stats[task_type]['failed'] += 1
    
    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'total_tasks': len(tms_system.tasks),
                'completed_tasks': len(completed_tasks),
                'failed_tasks': len(failed_tasks),
                'success_rate': len(completed_tasks) / len(tms_system.tasks) * 100 if tms_system.tasks else 0,
                'average_execution_time': avg_execution_time
            },
            'task_type_statistics': task_type_stats,
            'equipment_utilization': {
                eq.id: {
                    'name': eq.name,
                    'type': eq.__class__.__name__,
                    'status': eq.status.value,
                    'utilization_time': 0  # 这里需要实际的利用时间统计
                }
                for eq in tms_system.equipment.values()
            }
        },
        'generated_at': datetime.now().isoformat()
    })

# 日志API
@app.route('/api/logs', methods=['GET'])
@handle_api_errors
def get_execution_logs():
    """获取执行日志"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    logs = tms_system.execution_log[offset:offset + limit]
    
    return jsonify({
        'success': True,
        'data': {
            'logs': logs,
            'total_count': len(tms_system.execution_log),
            'limit': limit,
            'offset': offset
        }
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not Found',
        'message': '请求的资源不存在'
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad Request',
        'message': '请求参数错误'
    }), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal Server Error',
        'message': '服务器内部错误'
    }), 500

# 初始化系统数据
def initialize_demo_data():
    """初始化演示数据"""
    try:
        # 创建产品
        products = [
            Product("P001", "钢材", 10.0, 5.0, "金属", 5000.0),
            Product("P002", "水泥", 8.0, 4.0, "建材", 800.0),
            Product("P003", "木材", 5.0, 8.0, "建材", 1200.0),
            Product("P004", "玻璃", 3.0, 2.0, "建材", 1500.0),
            Product("P005", "塑料", 2.0, 6.0, "化工", 900.0)
        ]
        
        for product in products:
            tms_system.add_product(product)
        
        # 创建仓库
        terminal_wh1 = TerminalWarehouse("TW001", "末端库1", Position(0, 0), 1000.0)
        terminal_wh2 = TerminalWarehouse("TW002", "末端库2", Position(0, 19), 1200.0)
        product_wh1 = ProductWarehouse("PW001", "成品库1", Position(19, 0), 2000.0)
        product_wh2 = ProductWarehouse("PW002", "成品库2", Position(19, 19), 1800.0)
        
        tms_system.add_warehouse(terminal_wh1)
        tms_system.add_warehouse(terminal_wh2)
        tms_system.add_warehouse(product_wh1)
        tms_system.add_warehouse(product_wh2)
        
        # 创建设备
        crane1 = Crane("C001", "行车1", Position(0, 1), "TW001", 50.0)
        crane2 = Crane("C002", "行车2", Position(0, 18), "TW002", 50.0)
        crane3 = Crane("C003", "行车3", Position(19, 1), "PW001", 60.0)
        crane4 = Crane("C004", "行车4", Position(19, 18), "PW002", 60.0)
        
        truck1 = FrameTruck("T001", "车头1", Position(5, 5), 100.0)
        truck2 = FrameTruck("T002", "车头2", Position(15, 15), 100.0)
        
        frame1 = Frame("F001", "框架1", Position(5, 6), 80.0)
        frame2 = Frame("F002", "框架2", Position(15, 14), 80.0)
        
        equipment_list = [crane1, crane2, crane3, crane4, truck1, truck2, frame1, frame2]
        for equipment in equipment_list:
            tms_system.add_equipment(equipment)
        
        # 添加初始库存
        terminal_wh1.add_product("P001", 100, 5.0)
        terminal_wh1.add_product("P002", 80, 4.0)
        terminal_wh2.add_product("P003", 60, 8.0)
        terminal_wh2.add_product("P004", 40, 2.0)
        
        product_wh1.add_product("P005", 50, 6.0)
        
        logger.info("演示数据初始化完成")
        
    except Exception as e:
        logger.error(f"演示数据初始化失败: {e}")

# 应用启动
if __name__ == '__main__':
    # 初始化演示数据
    initialize_demo_data()
    
    # 启动应用
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    logger.info(f"TMS系统API服务启动在端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)