from osgeo import gdal, osr
import numpy as np

def txt_to_ascii_gdal(input_txt, output_file, cellsize, delimiter=',', nodata_value=-9999):
    """
    从TXT文件读取X,Y,Z数据并使用GDAL转换为ASCII Grid
    
    参数:
        input_txt - 输入TXT文件路径
        output_file - 输出文件路径
        cellsize - 栅格单元大小
        delimiter - 文本分隔符(默认为逗号)
        nodata_value - 无数据值
    """
    # 从TXT文件读取数据
    xyz_data = []
    with open(input_txt, 'r') as f:
        for line in f:
            line = line.strip()
            if line:  # 跳过空行
                parts = line.split(delimiter)
                if len(parts) >= 3:  # 确保至少有X,Y,Z三列
                    try:
                        x = float(parts[0].strip())
                        y = float(parts[1].strip())
                        z = float(parts[2].strip())
                        xyz_data.append((x, y, z))
                    except ValueError:
                        print(f"跳过无效行: {line}")

    if not xyz_data:
        raise ValueError("未找到有效的X,Y,Z数据")

    # 计算网格范围
    x_coords = [point[0] for point in xyz_data]
    y_coords = [point[1] for point in xyz_data]
    
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    
    # 计算行列数
    ncols = int(round((x_max - x_min) / cellsize)) + 1
    nrows = int(round((y_max - y_min) / cellsize)) + 1
    
    # 创建空网格
    grid = np.full((nrows, ncols), nodata_value, dtype=np.float32)
    
    # 填充网格
    for x, y, z in xyz_data:
        col = int(round((x - x_min) / cellsize))
        row = nrows - 1 - int(round((y - y_min) / cellsize))  # 反转Y轴
        if 0 <= row < nrows and 0 <= col < ncols:
            grid[row, col] = z
    
    # 创建GDAL数据集 - 关键修改点
    # 首先确保输出文件扩展名为.asc
    if not output_file.lower().endswith('.asc'):
        output_file += '.asc'
    
    # 使用正确的驱动名称
    driver = gdal.GetDriverByName('AAIGrid')
    if driver is None:
        raise RuntimeError("无法加载AAIGrid驱动，请确保GDAL支持此格式")
    
    # 创建临时内存数据集
    mem_driver = gdal.GetDriverByName('MEM')
    dataset = mem_driver.Create('', ncols, nrows, 1, gdal.GDT_Float32)
    
    # 设置地理参考
    dataset.SetGeoTransform((x_min, cellsize, 0, y_max, 0, -cellsize))
    
    # 设置投影
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # WGS84坐标系
    dataset.SetProjection(srs.ExportToWkt())
    
    # 写入数据
    band = dataset.GetRasterBand(1)
    band.WriteArray(grid)
    band.SetNoDataValue(nodata_value)
    
    # 创建实际输出文件
    driver.CreateCopy(output_file, dataset)
    
    # 关闭数据集
    dataset = None

# 示例使用
txt_to_ascii_gdal('input.txt', 'output_gdal.asc', cellsize=1.0)
