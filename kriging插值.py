import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import gstools as gs
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
# --- 步骤0：安装必要的库 ---   
#解决图片显示问
plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置中文显示
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
# --- 步骤1：读取Excel数据 ---
df = pd.read_excel('input.xlsx', engine='openpyxl')

# 解析第一列坐标（假设格式为"x,y"）
coordinates = df.iloc[:, 0].str.split(',', expand=True)
x = coordinates[0].astype(float).values  # 提取X坐标
y = coordinates[1].astype(float).values  # 提取Y坐标
z = df.iloc[:, 1].values  # 假设第二列为待插值属性值

# --- 步骤2：生成10m间隔的插值网格 ---
grid_x = np.arange(x.min(), x.max(), 50.0)  # X方向10米间隔
grid_y = np.arange(y.min(), y.max(), 50.0)  # Y方向10米间隔
xx, yy = np.meshgrid(grid_x, grid_y)  # 生成网格坐标矩阵

# --- 步骤3：拟合变异函数模型 ---
# 计算经验半变异函数
bin_center, gamma = gs.vario_estimate((x, y), z, return_counts=False)

# 自动拟合高斯模型参数
model = gs.Gaussian(dim=2, var=1, len_scale=1)
model.fit_variogram(bin_center, gamma, nugget=0.1)
print(f"拟合参数：方差={model.var}, 变程={model.len_scale}, 块金值={model.nugget}")

# --- 步骤4：执行克里金插值 ---
krige = gs.krige.Ordinary(model, cond_pos=[x, y], cond_val=z)
krige((xx, yy))  # 执行插值
z_interp = krige.field.reshape(xx.shape)  # 关键修复：确保 2D 形状

# --- 步骤5：保存结果到Excel（优化格式）---
# 创建DataFrame
result_df = pd.DataFrame({
    'X坐标(m)': xx.flatten(),
    'Y坐标(m)': yy.flatten(),
    '插值结果': z_interp.flatten()
})

# 使用openpyxl优化Excel格式
with pd.ExcelWriter('kriging_result_optimized.xlsx', engine='openpyxl') as writer:
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


# --- 步骤6：可视化结果 ---
plt.figure(figsize=(10, 8))
contour = plt.contourf(xx, yy, z_interp, cmap='viridis', levels=50)  # 现在 z_interp 是 2D
plt.colorbar(contour, label='插值结果')
plt.scatter(x, y, c='red', s=30, edgecolor='k', label='原始采样点')
plt.title(f'50m密度克里金插值 (GStools)\n模型: {model.name}, 变程={model.len_scale:.1f}m')
plt.xlabel('X坐标(m)')
plt.ylabel('Y坐标(m)')
plt.legend()
plt.savefig('kriging_gstools.png', dpi=300)
plt.show()
