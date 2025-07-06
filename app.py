#  """
# 厂区货物调度系统 - Web服务器

# 该模块提供Web界面和API接口，用于展示厂区货物调度系统的功能
# """

from flask import Flask, request, jsonify, render_template, send_from_directory
from test2.factory_logistics_system import *
import json
import uuid
from datetime import datetime, timedelta
import os

app = Flask(__name__, static_url_path='', static_folder='static')

# 全局系统实例
system = LogisticsSystem(grid_size=(15, 15))

# 初始化一些默认数据
def initialize_system():
    # 创建产品
    products = [
        Product("P001", "钢材", 10.0, 5.0),
        Product("P002", "水泥", 8.0, 4.0),
        Product("P003", "木材", 5.0, 8.0),
        Product("P004", "玻璃", 3.0, 2.0),
        Product("P005", "塑料", 2.0, 6.0)
    ]
    
    for product in products:
        system.add_product(product)
    
    # 创建末端库
    terminal_wh = TerminalWarehouse("TW001", "末端库1", Position(0, 0), 1000.0)
    terminal_wh.add_product("P001", 100)
    terminal_wh.add_product("P002", 80)
    system.add_terminal_warehouse(terminal_wh)
    
    # 创建成品库
    product_wh = ProductWarehouse("PW001", "成品库1", Position(0, 9), 2000.0)
    system.add_product_warehouse(product_wh)
    
    # 创建行车
    terminal_crane = Crane("C001", "末端库行车1", Position(0, 0), warehouse_id="TW001")
    product_crane = Crane("C002", "成品库行车1", Position(0, 9), warehouse_id="PW001")
    system.add_crane(terminal_crane)
    system.add_crane(product_crane)
    
    # 创建框架和车头
    frame = Frame("F001", "框架1", Position(5, 5))
    truck = FrameTruck("T001", "车头1", Position(5, 4))
    system.add_frame(frame)
    system.add_frame_truck(truck)

# 初始化系统
initialize_system()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/documentation')
def documentation():
    """系统文档"""
    with open("test2/system_documentation.md", 'r', encoding='utf-8') as f:
        content = f.read()
    return render_template('documentation.html', content=content)

@app.route('/api/system_status')
def get_system_status():
    """获取系统状态"""
    return jsonify(system.get_system_status())

@app.route('/api/resources')
def get_resources():
    """获取所有资源"""
    return jsonify({
        'terminal_warehouses': {k: {'id': v.id, 'name': v.name, 'position': {'x': v.position.x, 'y': v.position.y}, 
                                   'products': v.products} 
                               for k, v in system.terminal_warehouses.items()},
        'product_warehouses': {k: {'id': v.id, 'name': v.name, 'position': {'x': v.position.x, 'y': v.position.y}, 
                                  'products': v.products} 
                              for k, v in system.product_warehouses.items()},
        'cranes': {k: {'id': v.id, 'name': v.name, 'position': {'x': v.position.x, 'y': v.position.y}, 
                      'status': v.status.value, 'warehouse_id': v.warehouse_id} 
                  for k, v in system.cranes.items()},
        'frames': {k: {'id': v.id, 'name': v.name, 'position': {'x': v.position.x, 'y': v.position.y}, 
                      'status': v.status.value} 
                  for k, v in system.frames.items()},
        'frame_trucks': {k: {'id': v.id, 'name': v.name, 'position': {'x': v.position.x, 'y': v.position.y}, 
                            'status': v.status.value, 'attached_frame_id': v.attached_frame_id} 
                        for k, v in system.frame_trucks.items()},
        'products': {k: {'id': v.id, 'name': v.name, 'weight': v.weight, 'volume': v.volume} 
                    for k, v in system.products.items()}
    })

@app.route('/api/tasks')
def get_tasks():
    """获取所有任务"""
    return jsonify({
        task_id: {
            'id': task.id,
            'type': task.task_type.value,
            'status': task.status.value,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'sub_tasks': [{'id': st.id, 'type': st.task_type.value, 'status': st.status.value} for st in task.sub_tasks]
        } for task_id, task in system.tasks.items()
    })

@app.route('/api/add_product', methods=['POST'])
def add_product():
    """添加产品"""
    data = request.json
    product = Product(
        id=data.get('id', ''),
        name=data['name'],
        weight=float(data['weight']),
        volume=float(data['volume'])
    )
    system.add_product(product)
    return jsonify({'success': True, 'product': {'id': product.id, 'name': product.name}})

@app.route('/api/add_terminal_warehouse', methods=['POST'])
def add_terminal_warehouse():
    """添加末端库"""
    data = request.json
    warehouse = TerminalWarehouse(
        id=data.get('id', ''),
        name=data['name'],
        position=Position(int(data['position_x']), int(data['position_y'])),
        capacity=float(data['capacity'])
    )
    system.add_terminal_warehouse(warehouse)
    return jsonify({'success': True, 'warehouse': {'id': warehouse.id, 'name': warehouse.name}})

@app.route('/api/add_product_warehouse', methods=['POST'])
def add_product_warehouse():
    """添加成品库"""
    data = request.json
    warehouse = ProductWarehouse(
        id=data.get('id', ''),
        name=data['name'],
        position=Position(int(data['position_x']), int(data['position_y'])),
        capacity=float(data['capacity'])
    )
    system.add_product_warehouse(warehouse)
    return jsonify({'success': True, 'warehouse': {'id': warehouse.id, 'name': warehouse.name}})

@app.route('/api/add_crane', methods=['POST'])
def add_crane():
    """添加行车"""
    data = request.json
    crane = Crane(
        id=data.get('id', ''),
        name=data['name'],
        position=Position(int(data['position_x']), int(data['position_y'])),
        warehouse_id=data['warehouse_id']
    )
    system.add_crane(crane)
    return jsonify({'success': True, 'crane': {'id': crane.id, 'name': crane.name}})

@app.route('/api/add_frame', methods=['POST'])
def add_frame():
    """添加框架"""
    data = request.json
    frame = Frame(
        id=data.get('id', ''),
        name=data['name'],
        position=Position(int(data['position_x']), int(data['position_y']))
    )
    system.add_frame(frame)
    return jsonify({'success': True, 'frame': {'id': frame.id, 'name': frame.name}})

@app.route('/api/add_frame_truck', methods=['POST'])
def add_frame_truck():
    """添加框架车头"""
    data = request.json
    truck = FrameTruck(
        id=data.get('id', ''),
        name=data['name'],
        position=Position(int(data['position_x']), int(data['position_y']))
    )
    system.add_frame_truck(truck)
    return jsonify({'success': True, 'truck': {'id': truck.id, 'name': truck.name}})

@app.route('/api/create_ship_plan', methods=['POST'])
def create_ship_plan():
    """创建船运计划"""
    data = request.json
    plan = ShipPlan(
        id=data.get('id', ''),
        products=data['products'],
        deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else datetime.now() + timedelta(hours=2),
        priority=int(data.get('priority', 1))
    )
    system.add_ship_plan(plan)
    return jsonify({'success': True, 'plan': {'id': plan.id}})

@app.route('/api/create_ship_transport_task', methods=['POST'])
def create_ship_transport_task():
    """创建船运任务"""
    data = request.json
    task = system.create_ship_transport_task(data['plan_id'])
    if task:
        return jsonify({'success': True, 'task': {'id': task.id}})
    return jsonify({'success': False, 'message': '船运任务创建失败'})

@app.route('/api/create_internal_transfer_task', methods=['POST'])
def create_internal_transfer_task():
    """创建内转任务"""
    data = request.json
    task = system.create_internal_transfer_task(
        data['source_warehouse_id'],
        data['target_warehouse_id'],
        data['products']
    )
    if task:
        return jsonify({'success': True, 'task': {'id': task.id}})
    return jsonify({'success': False, 'message': '内转任务创建失败'})

@app.route('/api/execute_task', methods=['POST'])
def execute_task():
    """执行任务"""
    data = request.json
    success = system.execute_task(data['task_id'])
    return jsonify({'success': success, 'logs': system.execution_log[-10:]})

@app.route('/api/update_warehouse_product', methods=['POST'])
def update_warehouse_product():
    """更新仓库产品"""
    data = request.json
    warehouse_id = data['warehouse_id']
    product_id = data['product_id']
    quantity = int(data['quantity'])
    
    # 判断是末端库还是成品库
    if warehouse_id in system.terminal_warehouses:
        warehouse = system.terminal_warehouses[warehouse_id]
    elif warehouse_id in system.product_warehouses:
        warehouse = system.product_warehouses[warehouse_id]
    else:
        return jsonify({'success': False, 'message': '找不到指定仓库'})
    
    if quantity >= 0:
        success = warehouse.add_product(product_id, quantity)
    else:
        success = warehouse.remove_product(product_id, abs(quantity))
    
    return jsonify({'success': success})

@app.route('/api/reset_system', methods=['POST'])
def reset_system():
    """重置系统"""
    global system
    system = LogisticsSystem(grid_size=(15, 15))
    initialize_system()
    return jsonify({'success': True})

if __name__ == '__main__':
    # 检查并创建static和templates目录
    for folder in ['static', 'templates']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    app.run(debug=True)