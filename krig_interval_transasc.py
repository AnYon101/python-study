import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pykrige.ok import OrdinaryKriging
from pykrige.kriging_tools import write_asc_grid
from openpyxl.styles import PatternFill, Font, Alignment

# --- 中文显示设置 ---
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# --- 读取数据 ---
df = pd.read_excel('input.xlsx', engine='openpyxl')
x = df.iloc[:, 0].values
y = df.iloc[:, 1].values
z = df.iloc[:, 2].values

# --- 生成网格 ---
grid_x = np.arange(x.min(), x.max(), 5.0)
grid_y = np.arange(y.min(), y.max(), 5.0)
xx, yy = np.meshgrid(grid_x, grid_y)

# --- 克里金插值 ---
variogram_model = 'gaussian'  # 使用高斯模型'gaussian'，可选'linear', 'power', 'spherical', 'exponential'，'hole-effect'
ok = OrdinaryKriging(
    x, y, z,
    variogram_model=variogram_model,
    variogram_parameters={'sill': 2.0, 'range': 80, 'nugget': 0.1},
    verbose=False,
    enable_plotting=False
)
z_interp, ss = ok.execute('grid', grid_x, grid_y)
z_interp = z_interp.data

# --- 导出ASC文件 ---
write_asc_grid(grid_x, grid_y, z_interp, 'kriging_result.asc')

#插值结果可视化
plt.figure(figsize=(10, 8))
contour = plt.contourf(xx, yy, z_interp, cmap='viridis', levels=50)
plt.colorbar(contour, label='插值结果')
plt.gca().ticklabel_format(axis='both', style='plain', useOffset=False)  # 禁用XY轴科学计数法
plt.scatter(x, y, c='red', s=30, edgecolor='k', label='原始采样点')
plt.title(f'5m密度克里金插值\n模型:{ok.variogram_model}')
plt.xlabel('X坐标(m)')
plt.ylabel('Y坐标(m)')
plt.legend()
plt.savefig('kriging_pykrige.png', dpi=300)
plt.show()

# --- 保存到Excel ---
result_df = pd.DataFrame({
    'X坐标(m)': xx.flatten(),
    'Y坐标(m)': yy.flatten(),
    '插值结果': z_interp.flatten()
})

with pd.ExcelWriter('kriging_result_pykrige.xlsx', engine='openpyxl') as writer:
    result_df.to_excel(writer, sheet_name='插值结果', index=False)
    df.to_excel(writer, sheet_name='原始数据', index=False)
    
    workbook = writer.book
    sheet = workbook['插值结果']
    header_style = PatternFill(start_color="FFC000", fill_type="solid")
    for cell in sheet[1]:
        cell.fill = header_style
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
    sheet.column_dimensions['A'].width = 15
    sheet.column_dimensions['B'].width = 15
    sheet.column_dimensions['C'].width = 15
