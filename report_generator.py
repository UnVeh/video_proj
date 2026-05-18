from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from odm_defect_analyzer import analyze_segments_with_defects, ODM_DEFECTS


def meters_to_km_str(value):
    return f"{value // 1000}+{value % 1000:03d}"


def meters_to_km_float(length_m):
    return round(length_m / 1000, 3)


def process_report_data(report_data_forward, report_data_reverse=None):
    """
    Обрабатывает данные для отчета с учетом обратного направления
    Если обратное направление не указано, дублирует данные прямого направления
    Если указано, разворачивает их (так как километры идут в обратном порядке)
    """
    if not report_data_reverse:
        # Если нет обратного направления, дублируем прямое
        return report_data_forward, report_data_forward
    else:
        # Если есть обратное направление, разворачиваем его (так как километры идут в обратном порядке)
        # Сортируем по start (по возрастанию) - это развернет данные в правильном порядке
        reversed_data = sorted(report_data_reverse, key=lambda x: x[0])
        return report_data_forward, reversed_data


def flatten_defects(defects_list):
    """Преобразует список дефектов в плоский список уникальных кодов"""
    if not defects_list:
        return []
    
    codes = []
    for defect in defects_list:
        if isinstance(defect, dict):
            if "code" in defect:
                codes.append(str(defect["code"]))
        elif isinstance(defect, (int, float)):
            codes.append(str(defect))
        elif isinstance(defect, str):
            codes.append(defect)
    
    return list(set(codes))


def extract_defect_codes_for_gost(defects_list):
    """Извлекает коды дефектов для отчета ГОСТ"""
    if not defects_list:
        return []
    
    codes = []
    for defect in defects_list:
        if isinstance(defect, dict) and "code" in defect:
            codes.append(defect["code"])
        elif isinstance(defect, (int, float)):
            codes.append(int(defect))
    
    return list(set(codes))


def generate_excel(report_data_forward, report_data_reverse=None, filename="report.xlsx"):
    """Генерация отчета по ГОСТ"""
    # Обрабатываем данные (разворачиваем обратное направление если нужно)
    forward_data, reverse_data = process_report_data(report_data_forward, report_data_reverse)
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет ГОСТ"

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Заголовки
    ws.merge_cells("A1:A3")
    ws["A1"] = "№ участка диагностики"
    ws["A1"].alignment = center
    ws["A1"].font = bold

    ws.merge_cells("B1:B3")
    ws["B1"] = "Начало участка, км+м"
    ws["B1"].alignment = center
    ws["B1"].font = bold

    ws.merge_cells("C1:C3")
    ws["C1"] = "Конец участка, км+м"
    ws["C1"].alignment = center
    ws["C1"].font = bold

    ws.merge_cells("D1:D3")
    ws["D1"] = "Протяженность, км"
    ws["D1"].alignment = center
    ws["D1"].font = bold

    ws.merge_cells("E1:R1")
    ws["E1"] = "Наличие дефекта"
    ws["E1"].alignment = center
    ws["E1"].font = bold

    ws.merge_cells("E2:K2")
    ws["E2"] = "Прямое направление"
    ws["E2"].alignment = center
    ws["E2"].font = bold

    ws.merge_cells("L2:R2")
    ws["L2"] = "Обратное направление"
    ws["L2"].alignment = center
    ws["L2"].font = bold

    defect_names = [
        "Выбоина", "Пролом", "Просадка", "Сдвиг волна",
        "Гребенки", "Колея", "Необработанные места выпотевания вяжущего"
    ]

    for i, name in enumerate(defect_names, start=5):
        cell = ws.cell(row=3, column=i, value=name)
        cell.alignment = center
        cell.font = bold

    for i, name in enumerate(defect_names, start=12):
        cell = ws.cell(row=3, column=i, value=name)
        cell.alignment = center
        cell.font = bold

    ws.merge_cells("S1:S3")
    ws["S1"] = "Соответствует нормативному состоянию"
    ws["S1"].alignment = center
    ws["S1"].font = bold

    for row in range(1, 4):
        for col in range(1, 20):
            cell = ws.cell(row=row, column=col)
            cell.border = thin_border

    defect_map = {
        1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6
    }

    start_row = 4
    max_len = max(len(forward_data), len(reverse_data))
    
    for idx in range(max_len):
        row_num = start_row + idx
        
        if idx < len(forward_data):
            seg_start, seg_end, defects = forward_data[idx]
            num = idx + 1

            ws.cell(row=row_num, column=1, value=num)
            ws.cell(row=row_num, column=2, value=meters_to_km_str(seg_start))
            ws.cell(row=row_num, column=3, value=meters_to_km_str(seg_end))
            length_km = seg_end - seg_start
            cell = ws.cell(row=row_num, column=4, value=length_km / 1000)
            cell.number_format = '0.000'
            cell.border = thin_border
            
            defect_codes = extract_defect_codes_for_gost(defects)
            defects_marks = [""] * 7
            for d in defect_codes:
                if d in defect_map:
                    defects_marks[defect_map[d]] = "да"
            
            for i, val in enumerate(defects_marks, start=5):
                cell = ws.cell(row=row_num, column=i, value=val)
                cell.alignment = center
                cell.border = thin_border
        
        if idx < len(reverse_data):
            seg_start, seg_end, defects = reverse_data[idx]
            
            if idx >= len(forward_data):
                num = idx + 1
                ws.cell(row=row_num, column=1, value=num)
                ws.cell(row=row_num, column=2, value=meters_to_km_str(seg_start))
                ws.cell(row=row_num, column=3, value=meters_to_km_str(seg_end))
                ws.cell(row=row_num, column=4, value=meters_to_km_float(seg_end - seg_start))
            
            defect_codes = extract_defect_codes_for_gost(defects)
            defects_marks_reverse = [""] * 7
            for d in defect_codes:
                if d in defect_map:
                    defects_marks_reverse[defect_map[d]] = "да"
            
            for i, val in enumerate(defects_marks_reverse, start=12):
                cell = ws.cell(row=row_num, column=i, value=val)
                cell.alignment = center
                cell.border = thin_border
        
        has_defects_forward = False
        has_defects_reverse = False
        
        if idx < len(forward_data):
            defect_codes_forward = extract_defect_codes_for_gost(forward_data[idx][2])
            has_defects_forward = len(defect_codes_forward) > 0
        
        if idx < len(reverse_data):
            defect_codes_reverse = extract_defect_codes_for_gost(reverse_data[idx][2])
            has_defects_reverse = len(defect_codes_reverse) > 0
        
        overall_normal = "нет" if (has_defects_forward or has_defects_reverse) else "да"
        
        cell = ws.cell(row=row_num, column=19, value=overall_normal)
        cell.alignment = center
        cell.border = thin_border
        
        for col in range(1, 20):
            cell = ws.cell(row=row_num, column=col)
            cell.alignment = center
            cell.border = thin_border

    for col_idx, col in enumerate(ws.columns, start=1):
        max_length = 0
        col_letter = get_column_letter(col_idx)
        
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        
        ws.column_dimensions[col_letter].width = min(max_length + 2, 30)

    wb.save(filename)
    return filename


def generate_odm_excel(report_data_forward, report_data_reverse=None, filename="report_odm.xlsx"):
    """
    Генерация отчета по ОДМ с анализом дефектов по сегментам
    """
    from odm_defect_analyzer import analyze_segments_with_defects
    
    # ВАЖНО: Обрабатываем данные так же, как и для ГОСТ отчета
    # Разворачиваем обратное направление если оно есть
    forward_data, reverse_data = process_report_data(report_data_forward, report_data_reverse)
    
    # Анализируем дефекты и разбиваем на сегменты по 100м
    if forward_data:
        forward_segments = analyze_segments_with_defects(forward_data, segment_length=100)
    else:
        forward_segments = []
    
    if reverse_data:
        reverse_segments = analyze_segments_with_defects(reverse_data, segment_length=100)
    else:
        reverse_segments = []
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет ОДМ"

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    current_date = datetime.now().strftime("%d.%m.%Y")

    # Заголовки
    ws.merge_cells("A1:A2")
    ws["A1"] = "Начало участка, км+м"
    ws["A1"].alignment = center
    ws["A1"].font = bold

    ws.merge_cells("B1:B2")
    ws["B1"] = "Конец участка, км+м"
    ws["B1"].alignment = center
    ws["B1"].font = bold

    ws.merge_cells("C1:C2")
    ws["C1"] = "Протяженность, км"
    ws["C1"].alignment = center
    ws["C1"].font = bold

    ws.merge_cells("D1:D2")
    ws["D1"] = "Дата проведения обследования"
    ws["D1"].alignment = center
    ws["D1"].font = bold

    ws.merge_cells("E1:F1")
    ws["E1"] = "Коды дефектов по направлению движения"
    ws["E1"].alignment = center
    ws["E1"].font = bold
    
    ws["E2"] = "Прямое направление"
    ws["E2"].alignment = center
    ws["E2"].font = bold
    
    ws["F2"] = "Обратное направление"
    ws["F2"].alignment = center
    ws["F2"].font = bold

    ws.merge_cells("G1:H1")
    ws["G1"] = "Оценка в баллах"
    ws["G1"].alignment = center
    ws["G1"].font = bold
    
    ws["G2"] = "Прямое направление"
    ws["G2"].alignment = center
    ws["G2"].font = bold
    
    ws["H2"] = "Обратное направление"
    ws["H2"].alignment = center
    ws["H2"].font = bold

    ws.merge_cells("I1:I2")
    ws["I1"] = "Минимальная оценка в баллах"
    ws["I1"].alignment = center
    ws["I1"].font = bold

    ws.merge_cells("J1:J2")
    ws["J1"] = "Соответствие нормативному состоянию"
    ws["J1"].alignment = center
    ws["J1"].font = bold

    for row in range(1, 3):
        for col in range(1, 11):
            cell = ws.cell(row=row, column=col)
            cell.border = thin_border

    start_row = 3
    max_len = max(len(forward_segments), len(reverse_segments))
    
    for idx in range(max_len):
        row_num = start_row + idx
        
        # Данные прямого направления
        forward_defect_code = ""
        forward_score = 5.0
        
        if idx < len(forward_segments):
            seg_start, seg_end, (defect_code, score) = forward_segments[idx]
            
            ws.cell(row=row_num, column=1, value=meters_to_km_str(seg_start))
            ws.cell(row=row_num, column=2, value=meters_to_km_str(seg_end))
            length_km = seg_end - seg_start
            km_cell = ws.cell(row=row_num, column=3, value=length_km / 1000)
            km_cell.number_format = '0.000'
            km_cell.border = thin_border
            
            ws.cell(row=row_num, column=4, value=current_date)
            
            forward_defect_code = str(defect_code) if defect_code else ""
            forward_score = score
        
        # Данные обратного направления
        reverse_defect_code = ""
        reverse_score = 5.0
        
        if idx < len(reverse_segments):
            seg_start, seg_end, (defect_code, score) = reverse_segments[idx]
            
            if idx >= len(forward_segments):
                length_km = round((seg_end - seg_start) / 1000, 3)
                ws.cell(row=row_num, column=1, value=meters_to_km_str(seg_start))
                ws.cell(row=row_num, column=2, value=meters_to_km_str(seg_end))
                ws.cell(row=row_num, column=3, value=length_km)
                ws.cell(row=row_num, column=4, value=current_date)
            
            reverse_defect_code = str(defect_code) if defect_code else ""
            reverse_score = score
        
        # Заполняем ячейки
        if idx < len(forward_segments) or idx < len(reverse_segments):
            ws.cell(row=row_num, column=5, value=forward_defect_code)
            ws.cell(row=row_num, column=6, value=reverse_defect_code)
            ws.cell(row=row_num, column=7, value=forward_score)
            ws.cell(row=row_num, column=8, value=reverse_score)
            
            min_score = min(forward_score, reverse_score)
            ws.cell(row=row_num, column=9, value=min_score)
            
            is_normal = "да" if min_score >= 4.0 else "нет"
            ws.cell(row=row_num, column=10, value=is_normal)
        
        # Применяем форматирование
        for col in range(1, 11):
            cell = ws.cell(row=row_num, column=col)
            cell.alignment = center
            cell.border = thin_border
            
            if col in [7, 8, 9] and isinstance(cell.value, (int, float)):
                cell.number_format = '0.0'

    # Автоширина колонок
    for col_idx, col in enumerate(ws.columns, start=1):
        max_length = 0
        col_letter = get_column_letter(col_idx)
        
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        
        ws.column_dimensions[col_letter].width = min(max_length + 2, 25)

    wb.save(filename)
    return filename