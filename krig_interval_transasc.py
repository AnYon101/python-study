import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pykrige.ok import OrdinaryKriging  # 修改1：导入PyKrige的普通克里金类
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from pykrige.kriging_tools import write_asc_grid 

# --- 步骤0：设置中文显示 ---
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文显示
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# --- 步骤1：读取Excel数据 ---
df = pd.read_excel('input.xlsx', engine='openpyxl')

# 假设第一列为X坐标，第二列为Y坐标，第三列为Z值
x = df.iloc[:, 0].values  # 提取X坐标
y = df.iloc[:, 1].values  # 提取Y坐标
z = df.iloc[:, 2].values  # 提取Z值

# --- 步骤2：生成5m间隔的插值网格 ---
grid_x = np.arange(x.min(), x.max(), 5.0)  # X方向5米间隔
grid_y = np.arange(y.min(), y.max(), 5.0)  # Y方向5米间隔
xx, yy = np.meshgrid(grid_x, grid_y)  # 生成网格坐标矩阵

# --- 步骤3：使用PyKrige执行普通克里金插值（带搜索参数）---
# 设置搜索参数
#max_dist = 100  # 搜索半径（米）
#n_closest = 20  # 使用最近的12个点
#max_points = 100  # 最大使用点数
# (可选)min_points = 50  # 最少使用5个点
# --- 步骤4：使用PyKrige执行普通克里金插值 ---
# 注意：PyKrige会自动拟合变异函数模型
ok = OrdinaryKriging(
    x, y, z,
    variogram_model='spherical',  # 使用高斯模型'gaussian'，可选'linear', 'power', 'spherical', 'exponential'，'hole-effect'
    verbose=False,
    enable_plotting=False
)

# 步骤5：执行网格插值，z_interp是插值结果，ss是方差
z_interp, ss = ok.execute('grid', grid_x, grid_y)
z_interp = z_interp.data  # 获取插值结果的numpy数组

# --- 步骤4：导出ASC文件 ---
write_asc_grid(grid_x, grid_y, z_interp, 'kriging_result.asc' )
# 可选：指定单元格大小（需与网格间距一致）

# --- 步骤:6：保存结果到Excel（优化格式）---
# 创建DataFrame
result_df = pd.DataFrame({
    'X坐标(m)': xx.flatten(),
    'Y坐标(m)': yy.flatten(),
    '插值结果': z_interp.flatten()
})

# 使用openpyxl优化Excel格式
with pd.ExcelWriter('kriging_result_pykrige.xlsx', engine='openpyxl') as writer:
    # Sheet1: 插值结果（格式化）
    result_df.to_excel(writer, sheet_name='插值结果', index=False)
    
    # Sheet2: 原始数据（可选）
    df.to_excel(writer, sheet_name='原始数据', index=False)
    
    # 获取Excel工作簿对象
    workbook = writer.book
    sheet = workbook['插值结果']
    
    # 设置表头样式
    header_fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
    header_font = Font(bold=True, color="000000")
    
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
    
    # 设置列宽
    sheet.column_dimensions['A'].width = 15
    sheet.column_dimensions['B'].width = 15
    sheet.column_dimensions['C'].width = 15

# --- 步骤7：可视化结果 ---
plt.figure(figsize=(10, 8))
contour = plt.contourf(xx, yy, z_interp, cmap='viridis', levels=50)
plt.colorbar(contour, label='插值结果')
plt.scatter(x, y, c='red', s=30, edgecolor='k', label='原始采样点')
plt.title('5m密度克里金插值 (PyKrige)\n模型:spherical ')
plt.xlabel('X坐标(m)')
plt.ylabel('Y坐标(m)')
plt.legend()
plt.savefig('kriging_pykrige.png', dpi=300)
plt.show()
