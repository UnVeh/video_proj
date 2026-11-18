from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import os


def meters_to_km_str(value):
    """Преобразует метры в формат км+м"""
    value = int(value)
    return f"{value // 1000}+{value % 1000:03d}"


def split_into_100m_segments(segments_data, common_start=None, common_end=None):
    """
    Разбивает сегменты на 100-метровые интервалы, выровненные по common_start.
    Возвращает dict: (start, end) -> list of defects (None = не покрыт).
    """
    if not segments_data:
        return {}
    
    if common_start is None:
        common_start = min(min(s[0], s[1]) for s in segments_data)
    if common_end is None:
        common_end = max(max(s[0], s[1]) for s in segments_data)
    
    interval_map = {}
    current = common_start
    while current < common_end:
        seg_end = min(current + 100, common_end)
        interval_map[(current, seg_end)] = None  # None = не покрыт
        current = seg_end
    
    for seg_start, seg_end, defects in segments_data:
        lo = min(seg_start, seg_end)
        hi = max(seg_start, seg_end)
        
        for (int_start, int_end) in interval_map.keys():
            overlap_start = max(lo, int_start)
            overlap_end = min(hi, int_end)
            if overlap_start < overlap_end:
                # Интервал покрыт — если был None, заменяем на []
                if interval_map[(int_start, int_end)] is None:
                    interval_map[(int_start, int_end)] = []
                for d in defects:
                    if isinstance(d, dict):
                        pos = d.get("position", (lo + hi) / 2)
                    else:
                        pos = (lo + hi) / 2
                    if int_start <= pos < int_end:
                        interval_map[(int_start, int_end)].append(d)
    
    return interval_map


def process_report_data(report_data_forward, report_data_reverse=None):
    """
    Обрабатывает данные для отчета.
    Возвращает: forward_sorted, reverse_sorted, common_start, common_end
    """
    fwd_sorted = sorted(report_data_forward, key=lambda x: x[0]) if report_data_forward else []
    rev_sorted = sorted(report_data_reverse, key=lambda x: x[0]) if report_data_reverse else []
    
    all_starts = [min(s[0], s[1]) for s in fwd_sorted] + [min(s[0], s[1]) for s in rev_sorted]
    all_ends = [max(s[0], s[1]) for s in fwd_sorted] + [max(s[0], s[1]) for s in rev_sorted]
    
    if all_starts and all_ends:
        common_start = min(all_starts)
        common_end = max(all_ends)
        print(f"Общий диапазон: {common_start} - {common_end} "
              f"(forward: {len(fwd_sorted)}, reverse: {len(rev_sorted)})")
    else:
        common_start = None
        common_end = None
    
    return fwd_sorted, rev_sorted, common_start, common_end


def extract_defect_codes_for_gost(defects_list):
    """Извлекает коды дефектов для отчета ГОСТ (6 классов)"""
    if not defects_list:
        return []
    
    codes = []
    for defect in defects_list:
        if isinstance(defect, dict):
            if "code" in defect:
                code = defect["code"]
                if isinstance(code, (int, float)):
                    codes.append(int(code))
                elif isinstance(code, str) and code.isdigit():
                    codes.append(int(code))
            elif "defect_code" in defect:
                code = defect["defect_code"]
                if isinstance(code, (int, float)):
                    codes.append(int(code))
                elif isinstance(code, str) and code.isdigit():
                    codes.append(int(code))
            elif "type" in defect:
                type_to_code = {
                    "pothole": 1, "subsidence": 2, "crack_grid": 3,
                    "crack_transverse": 4, "sealed_crack": 5, "collapse": 6,
                }
                if defect["type"] in type_to_code:
                    codes.append(type_to_code[defect["type"]])
        elif isinstance(defect, (int, float)):
            codes.append(int(defect))
        elif isinstance(defect, str) and defect.isdigit():
            codes.append(int(defect))
    
    return list(set(codes))


def generate_gost_report(forward_segments, reverse_segments, road_name, output_dir="reports"):
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        raise PermissionError(f"Не удалось создать директорию для отчета: {e}")
    
    safe_road_name = "".join(c for c in road_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"ГОСТ_{safe_road_name}_{timestamp}.xlsx")
    
    print(f"\n=== Генерация ГОСТ отчета для {road_name} ===")
    print(f"Исходные данные: forward={len(forward_segments) if forward_segments else 0}, "
          f"reverse={len(reverse_segments) if reverse_segments else 0}")
    
    forward_processed, reverse_processed, common_start, common_end = process_report_data(
        forward_segments, reverse_segments
    )
    
    # Выравниваем оба направления по общему диапазону
    forward_map = split_into_100m_segments(forward_processed, common_start, common_end) if forward_processed else {}
    reverse_map = split_into_100m_segments(reverse_processed, common_start, common_end) if reverse_processed else {}
    
    # Единый список интервалов
    all_intervals = []
    if common_start is not None and common_end is not None:
        current = common_start
        while current < common_end:
            seg_end = min(current + 100, common_end)
            all_intervals.append((current, seg_end))
            current = seg_end
    
    print(f"Всего строк таблицы: {len(all_intervals)}")
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет ГОСТ"

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

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

    ws.merge_cells("E1:P1")
    ws["E1"] = "Наличие дефекта"
    ws["E1"].alignment = center
    ws["E1"].font = bold

    ws.merge_cells("E2:J2")
    ws["E2"] = "Прямое направление"
    ws["E2"].alignment = center
    ws["E2"].font = bold

    ws.merge_cells("K2:P2")
    ws["K2"] = "Обратное направление"
    ws["K2"].alignment = center
    ws["K2"].font = bold

    defect_names = ["Выбоина", "Просадка", "Гребенка", "Колея", "Пучина", "Размыв"]
    for i, name in enumerate(defect_names, start=5):
        cell = ws.cell(row=3, column=i, value=name)
        cell.alignment = center
        cell.font = bold
    for i, name in enumerate(defect_names, start=11):
        cell = ws.cell(row=3, column=i, value=name)
        cell.alignment = center
        cell.font = bold

    ws.merge_cells("Q1:Q3")
    ws["Q1"] = "Соответствует нормативному состоянию"
    ws["Q1"].alignment = center
    ws["Q1"].font = bold

    ws.merge_cells("R1:R3")
    ws["R1"] = "Дата размещения сведений"
    ws["R1"].alignment = center
    ws["R1"].font = bold

    for row in range(1, 4):
        for col in range(1, 19):
            ws.cell(row=row, column=col).border = thin_border

    defect_map = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}

    start_row = 4
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    has_forward_direction = bool(forward_processed)
    has_reverse_direction = bool(reverse_processed)
    
    for idx, interval in enumerate(all_intervals):
        row_num = start_row + idx
        num = idx + 1
        seg_start, seg_end = interval
        
        ws.cell(row=row_num, column=1, value=num)
        ws.cell(row=row_num, column=2, value=meters_to_km_str(seg_start))
        ws.cell(row=row_num, column=3, value=meters_to_km_str(seg_end))
        cell = ws.cell(row=row_num, column=4, value=(seg_end - seg_start) / 1000)
        cell.number_format = '0.000'
        
        fwd_defects = forward_map.get(interval, None)
        rev_defects = reverse_map.get(interval, None)
        
        # Дублирование, если направления нет полностью
        if not has_reverse_direction and has_forward_direction:
            rev_defects = list(fwd_defects) if fwd_defects else []
        elif not has_forward_direction and has_reverse_direction:
            fwd_defects = list(rev_defects) if rev_defects else []
        # Дублирование, если конкретный интервал не покрыт одним направлением
        elif fwd_defects is None and rev_defects is not None:
            fwd_defects = list(rev_defects) if rev_defects else []
        elif rev_defects is None and fwd_defects is not None:
            rev_defects = list(fwd_defects) if fwd_defects else []
        
        codes = extract_defect_codes_for_gost(fwd_defects) if fwd_defects else []
        marks = [""] * 6
        for d in codes:
            if d in defect_map:
                marks[defect_map[d]] = "да"
        
        codes_rev = extract_defect_codes_for_gost(rev_defects) if rev_defects else []
        marks_rev = [""] * 6
        for d in codes_rev:
            if d in defect_map:
                marks_rev[defect_map[d]] = "да"
        
        for i, val in enumerate(marks, start=5):
            cell = ws.cell(row=row_num, column=i, value=val)
            cell.alignment = center
        for i, val in enumerate(marks_rev, start=11):
            cell = ws.cell(row=row_num, column=i, value=val)
            cell.alignment = center
        
        has_fwd = any(m == "да" for m in marks)
        has_rev = any(m == "да" for m in marks_rev)
        overall_normal = "нет" if (has_fwd or has_rev) else "да"
        
        ws.cell(row=row_num, column=17, value=overall_normal).alignment = center
        ws.cell(row=row_num, column=18, value=current_date).alignment = center
        
        for col in range(1, 19):
            cell = ws.cell(row=row_num, column=col)
            cell.border = thin_border
            cell.alignment = center

    for col_idx, col in enumerate(ws.columns, start=1):
        max_length = 0
        col_letter = get_column_letter(col_idx)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        if col_idx == 18:
            ws.column_dimensions[col_letter].width = 20
        else:
            ws.column_dimensions[col_letter].width = min(max_length + 2, 30)

    wb.save(filename)
    print(f"\nОтчет сохранен: {filename}")
    return filename


def generate_odm_report(forward_segments, reverse_segments, road_name, output_dir="reports"):
    from odm_defect_analyzer import analyze_segments_with_defects
    
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        raise PermissionError(f"Не удалось создать директорию для отчета: {e}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_road_name = "".join(c for c in road_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = os.path.join(output_dir, f"ОДМ_{safe_road_name}_{timestamp}.xlsx")
    
    print(f"\n=== Генерация ОДМ отчета для {road_name} ===")
    print(f"forward_data: {len(forward_segments) if forward_segments else 0} сегментов")
    print(f"reverse_data: {len(reverse_segments) if reverse_segments else 0} сегментов")
    
    forward_data, reverse_data, common_start, common_end = process_report_data(
        forward_segments, reverse_segments
    )
    
    # Выравниваем по общей сетке 100м
    forward_aligned = split_into_100m_segments(forward_data, common_start, common_end) if forward_data else {}
    reverse_aligned = split_into_100m_segments(reverse_data, common_start, common_end) if reverse_data else {}
    
    # Список 100-метровых интервалов
    all_intervals = []
    if common_start is not None and common_end is not None:
        current = common_start
        while current < common_end:
            seg_end = min(current + 100, common_end)
            all_intervals.append((current, seg_end))
            current = seg_end
    
    # Анализируем ОДМ для каждого интервала
    # Передаём сегменты в analyze_segments_with_defects
    forward_segs_list = [(k[0], k[1], v) for k, v in forward_aligned.items() if v is not None]
    reverse_segs_list = [(k[0], k[1], v) for k, v in reverse_aligned.items() if v is not None]
    
    forward_analyzed = analyze_segments_with_defects(forward_segs_list, segment_length=100) if forward_segs_list else []
    reverse_analyzed = analyze_segments_with_defects(reverse_segs_list, segment_length=100) if reverse_segs_list else []
    
    forward_map = {(s, e): (code, score) for s, e, (code, score) in forward_analyzed}
    reverse_map = {(s, e): (code, score) for s, e, (code, score) in reverse_analyzed}
    
    print(f"Всего строк таблицы: {len(all_intervals)}")
    print(f"forward_map keys: {list(forward_map.keys())[:3]}...")
    print(f"reverse_map keys: {list(reverse_map.keys())[:3]}...")
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет ОДМ"

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    bold = Font(bold=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )

    current_date = datetime.now().strftime("%d.%m.%Y")

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
            ws.cell(row=row, column=col).border = thin_border

        start_row = 3
    
    has_forward_direction = bool(forward_data)
    has_reverse_direction = bool(reverse_data)
    
    for idx, interval in enumerate(all_intervals):
        row_num = start_row + idx
        seg_start, seg_end = interval
        
        fwd = forward_map.get(interval)
        rev = reverse_map.get(interval)
        
        # Дублирование, если направления нет полностью
        if not has_reverse_direction and has_forward_direction:
            if fwd is not None:
                rev = fwd
        elif not has_forward_direction and has_reverse_direction:
            if rev is not None:
                fwd = rev
        # Дублирование, если конкретный интервал не покрыт одним направлением
        elif fwd is None and rev is not None:
            fwd = rev
        elif rev is None and fwd is not None:
            rev = fwd
        
        if fwd is None and rev is None:
            fwd_code, fwd_score = "", ""
            rev_code, rev_score = "", ""
        elif fwd is None:
            fwd_code, fwd_score = rev
            rev_code, rev_score = rev
        elif rev is None:
            fwd_code, fwd_score = fwd
            rev_code, rev_score = fwd
        else:
            fwd_code, fwd_score = fwd
            rev_code, rev_score = rev
        
        
        ws.cell(row=row_num, column=1, value=meters_to_km_str(seg_start))
        ws.cell(row=row_num, column=2, value=meters_to_km_str(seg_end))
        cell = ws.cell(row=row_num, column=3, value=(seg_end - seg_start) / 1000)
        cell.number_format = '0.000'
        ws.cell(row=row_num, column=4, value=current_date)
        
        ws.cell(row=row_num, column=5, value=str(fwd_code) if fwd_code != "" else "")
        ws.cell(row=row_num, column=6, value=str(rev_code) if rev_code != "" else "")
        ws.cell(row=row_num, column=7, value=fwd_score if fwd_score != "" else "")
        ws.cell(row=row_num, column=8, value=rev_score if rev_score != "" else "")
        
        scores = [s for s in [fwd_score, rev_score] if isinstance(s, (int, float))]
        if scores:
            min_score = min(scores)
            ws.cell(row=row_num, column=9, value=min_score)
            ws.cell(row=row_num, column=10, value="да" if min_score >= 4.0 else "нет")
        else:
            ws.cell(row=row_num, column=9, value="")
            ws.cell(row=row_num, column=10, value="")
        
        for col in range(1, 11):
            cell = ws.cell(row=row_num, column=col)
            cell.alignment = center
            cell.border = thin_border
            if col in [7, 8, 9] and isinstance(cell.value, (int, float)):
                cell.number_format = '0.1'

    for col_idx, col in enumerate(ws.columns, start=1):
        max_length = 0
        col_letter = get_column_letter(col_idx)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 25)

    wb.save(filename)
    print(f"\nОтчет сохранен: {filename}")
    return filename