#!/usr/bin/env python3
"""
TMS运输管理系统演示脚本
Transportation Management System Demo Script

该脚本演示了TMS系统的主要功能，包括：
- 系统初始化
- 产品、仓库、设备管理
- 任务创建和执行
- 性能报告生成
"""

import json
import time
from datetime import datetime, timedelta

from tms_system import (
    TMSSystem, Product, TerminalWarehouse, ProductWarehouse,
    Crane, FrameTruck, Frame, Position, ShipPlan
)

def print_separator(title: str):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f" {title} ")
    print("="*60)

def print_json(data, title: str = ""):
    """格式化打印JSON数据"""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

def demo_system_initialization():
    """演示系统初始化"""
    print_separator("TMS系统初始化演示")
    
    # 创建TMS系统实例
    print("🚀 创建TMS系统实例...")
    tms = TMSSystem(grid_size=(15, 15))
    print(f"✅ TMS系统初始化完成，网格大小: {tms.grid_size}")
    
    return tms

def demo_product_management(tms: TMSSystem):
    """演示产品管理"""
    print_separator("产品管理演示")
    
    # 创建产品
    products = [
        Product("P001", "钢材", 10.0, 5.0, "金属", 5000.0),
        Product("P002", "水泥", 8.0, 4.0, "建材", 800.0),
        Product("P003", "木材", 5.0, 8.0, "建材", 1200.0),
        Product("P004", "玻璃", 3.0, 2.0, "建材", 1500.0),
        Product("P005", "塑料", 2.0, 6.0, "化工", 900.0)
    ]
    
    print("📦 添加产品到系统...")
    for product in products:
        success = tms.add_product(product)
        status = "✅" if success else "❌"
        print(f"{status} 产品 {product.name} (ID: {product.id})")
    
    print(f"\n📊 系统中共有 {len(tms.products)} 个产品")
    
    # 显示产品详情
    print("\n产品详情:")
    for product_id, product in tms.products.items():
        print(f"  {product.id}: {product.name} - {product.weight}吨/{product.volume}m³ - ¥{product.unit_price}")

def demo_warehouse_management(tms: TMSSystem):
    """演示仓库管理"""
    print_separator("仓库管理演示")
    
    # 创建仓库
    warehouses = [
        TerminalWarehouse("TW001", "末端库1", Position(0, 0), 1000.0),
        TerminalWarehouse("TW002", "末端库2", Position(0, 14), 1200.0),
        ProductWarehouse("PW001", "成品库1", Position(14, 0), 2000.0),
        ProductWarehouse("PW002", "成品库2", Position(14, 14), 1800.0)
    ]
    
    print("🏭 添加仓库到系统...")
    for warehouse in warehouses:
        success = tms.add_warehouse(warehouse)
        status = "✅" if success else "❌"
        print(f"{status} 仓库 {warehouse.name} (ID: {warehouse.id}) - 位置: {warehouse.position}")
    
    # 添加初始库存
    print("\n📥 添加初始库存...")
    tms.warehouses["TW001"].add_product("P001", 100, 5.0)  # 钢材
    tms.warehouses["TW001"].add_product("P002", 80, 4.0)   # 水泥
    tms.warehouses["TW002"].add_product("P003", 60, 8.0)   # 木材
    tms.warehouses["TW002"].add_product("P004", 40, 2.0)   # 玻璃
    tms.warehouses["PW001"].add_product("P005", 50, 6.0)   # 塑料
    
    print("✅ 库存添加完成")
    
    # 显示仓库状态
    print("\n📊 仓库状态:")
    for warehouse_id, warehouse in tms.warehouses.items():
        utilization = warehouse.get_utilization_rate()
        print(f"  {warehouse.name}: 利用率 {utilization:.1f}% - 产品数量 {sum(warehouse.products.values())}")

def demo_equipment_management(tms: TMSSystem):
    """演示设备管理"""
    print_separator("设备管理演示")
    
    # 创建设备
    equipment_list = [
        Crane("C001", "行车1", Position(0, 1), "TW001", 50.0),
        Crane("C002", "行车2", Position(0, 13), "TW002", 50.0),
        Crane("C003", "行车3", Position(14, 1), "PW001", 60.0),
        Crane("C004", "行车4", Position(14, 13), "PW002", 60.0),
        FrameTruck("T001", "车头1", Position(7, 7), 100.0),
        FrameTruck("T002", "车头2", Position(8, 8), 100.0),
        Frame("F001", "框架1", Position(7, 8), 80.0),
        Frame("F002", "框架2", Position(8, 7), 80.0)
    ]
    
    print("🚛 添加设备到系统...")
    for equipment in equipment_list:
        success = tms.add_equipment(equipment)
        status = "✅" if success else "❌"
        equipment_type = equipment.__class__.__name__
        print(f"{status} {equipment_type} {equipment.name} (ID: {equipment.id}) - 位置: {equipment.position}")
    
    print(f"\n📊 系统中共有 {len(tms.equipment)} 台设备")
    
    # 显示设备状态
    print("\n设备状态:")
    for equipment_id, equipment in tms.equipment.items():
        equipment_type = equipment.__class__.__name__
        print(f"  {equipment.name} ({equipment_type}): {equipment.status.value}")

def demo_task_management(tms: TMSSystem):
    """演示任务管理"""
    print_separator("任务管理演示")
    
    # 创建船运计划和任务
    print("🚢 创建船运任务...")
    ship_plan = ShipPlan(
        "SP001",
        {"P005": 20, "P001": 15},  # 塑料20个，钢材15个
        datetime.now() + timedelta(hours=4),
        priority=2,
        ship_name="货轮001",
        destination="上海港"
    )
    
    tms.ship_plans[ship_plan.id] = ship_plan
    ship_task = tms.create_ship_transport_task(ship_plan)
    
    if ship_task:
        print(f"✅ 船运任务创建成功 (ID: {ship_task.id})")
        print(f"   计划: {ship_plan.ship_name} -> {ship_plan.destination}")
        print(f"   货物: {ship_plan.products}")
    
    # 创建内转任务
    print("\n🔄 创建内转任务...")
    transfer_task = tms.create_internal_transfer_task(
        "TW001", "PW001", {"P001": 10, "P002": 15}
    )
    
    if transfer_task:
        print(f"✅ 内转任务创建成功 (ID: {transfer_task.id})")
        print(f"   从末端库1转移到成品库1: 钢材10个, 水泥15个")
    
    print(f"\n📊 系统中共有 {len(tms.tasks)} 个任务")

def demo_task_scheduling_and_execution(tms: TMSSystem):
    """演示任务调度和执行"""
    print_separator("任务调度与执行演示")
    
    # 优化任务调度
    print("🧠 优化任务调度...")
    schedule = tms.optimize_task_schedule()
    
    if schedule:
        print(f"✅ 调度优化完成，共 {len(schedule)} 个任务被分配")
        for i, task_id in enumerate(schedule, 1):
            task = tms.tasks[task_id]
            print(f"  {i}. 任务 {task_id} ({task.task_type.value}) - 优先级: {task.priority}")
    else:
        print("⚠️ 没有可调度的任务")
    
    # 执行任务
    if schedule:
        print("\n⚡ 执行任务...")
        executed_count = 0
        for task_id in schedule:
            print(f"正在执行任务 {task_id}...")
            success = tms.execute_task(task_id)
            status = "✅ 成功" if success else "❌ 失败"
            print(f"  {status}")
            if success:
                executed_count += 1
            time.sleep(0.5)  # 模拟执行时间
        
        print(f"\n📊 任务执行完成: {executed_count}/{len(schedule)} 成功")

def demo_path_planning(tms: TMSSystem):
    """演示路径规划"""
    print_separator("路径规划演示")
    
    print("🗺️ 演示设备路径规划...")
    
    # 选择一台设备进行路径规划演示
    if tms.equipment:
        equipment_id = list(tms.equipment.keys())[0]
        equipment = tms.equipment[equipment_id]
        
        start_pos = equipment.position
        target_pos = Position(10, 10)
        
        print(f"设备: {equipment.name}")
        print(f"起始位置: {start_pos}")
        print(f"目标位置: {target_pos}")
        
        # 计算路径
        path = tms.path_planner.a_star_path(start_pos, target_pos)
        
        if path:
            print(f"✅ 路径规划成功，共 {len(path)} 个节点")
            print("路径详情:")
            for i, pos in enumerate(path):
                if i == 0:
                    print(f"  起点: {pos}")
                elif i == len(path) - 1:
                    print(f"  终点: {pos}")
                else:
                    print(f"  节点{i}: {pos}")
        else:
            print("❌ 无法找到有效路径")

def demo_system_monitoring(tms: TMSSystem):
    """演示系统监控"""
    print_separator("系统监控演示")
    
    # 获取系统状态
    print("📊 获取系统状态...")
    status = tms.get_system_status()
    print_json(status, "系统状态")
    
    # 生成系统报告
    print("\n📈 生成系统报告...")
    report = tms.generate_report()
    
    # 显示关键指标
    print("\n关键性能指标:")
    performance = report['performance_metrics']
    print(f"  完成任务数: {performance['total_completed_tasks']}")
    print(f"  平均执行时间: {performance['average_execution_time']:.2f}秒")
    print(f"  任务成功率: {performance['task_success_rate']:.1f}%")
    
    # 显示资源利用率
    print("\n资源利用率:")
    for wh_id, wh_info in report['resource_utilization']['warehouse_utilization'].items():
        print(f"  {wh_info['name']}: {wh_info['utilization_rate']:.1f}%")

def demo_execution_logs(tms: TMSSystem):
    """演示执行日志"""
    print_separator("执行日志演示")
    
    print("📝 最近的执行日志:")
    recent_logs = tms.execution_log[-10:]  # 最近10条日志
    
    if recent_logs:
        for i, log in enumerate(recent_logs, 1):
            print(f"  {i}. {log}")
    else:
        print("  暂无执行日志")

def main():
    """主演示函数"""
    print("🎯 TMS运输管理系统功能演示")
    print("Transportation Management System Demo")
    print("=" * 60)
    
    try:
        # 1. 系统初始化
        tms = demo_system_initialization()
        
        # 2. 产品管理
        demo_product_management(tms)
        
        # 3. 仓库管理
        demo_warehouse_management(tms)
        
        # 4. 设备管理
        demo_equipment_management(tms)
        
        # 5. 任务管理
        demo_task_management(tms)
        
        # 6. 任务调度和执行
        demo_task_scheduling_and_execution(tms)
        
        # 7. 路径规划
        demo_path_planning(tms)
        
        # 8. 系统监控
        demo_system_monitoring(tms)
        
        # 9. 执行日志
        demo_execution_logs(tms)
        
        print_separator("演示完成")
        print("🎉 TMS系统功能演示完成！")
        print("✨ 系统运行正常，所有核心功能已验证")
        
        # 提供后续操作建议
        print("\n💡 后续操作建议:")
        print("1. 启动API服务: python tms_api.py")
        print("2. 访问API文档: http://localhost:5000")
        print("3. 查看系统状态: http://localhost:5000/api/system/status")
        print("4. 运行测试: pytest")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        print("请检查系统配置和依赖是否正确安装")
        raise

if __name__ == "__main__":
    main()