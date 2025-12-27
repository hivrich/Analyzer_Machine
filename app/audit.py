"""
Audit Layer для проверки данных, выводов и гипотез.

Каждая цифра, вывод, гипотеза должны пройти строгий аудит перед попаданием в отчет.
Этот модуль реализует механизм "devil's advocate" - ставит под сомнение каждое утверждение.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
from datetime import datetime


@dataclass
class AuditResult:
    """Результат аудита одного утверждения"""
    claim: str  # Утверждение
    status: str  # passed | failed | warning
    evidence: List[str]  # Источники данных
    issues: List[str]  # Найденные проблемы
    alternative_hypotheses: List[str]  # Альтернативные объяснения
    confidence: float  # Уверенность в утверждении (0-1)


@dataclass
class DataPoint:
    """Одна точка данных для аудита"""
    metric: str  # Название метрики
    value: Any  # Значение
    source_file: str  # Откуда взято
    period: str  # Период
    context: Dict[str, Any]  # Дополнительный контекст


class AuditEngine:
    """
    Движок аудита данных и выводов.
    
    Принципы:
    1. Каждая цифра должна иметь источник
    2. Каждый вывод должен быть обоснован данными
    3. Каждая гипотеза должна иметь альтернативы
    4. Расчеты должны быть проверены
    5. Данные из разных источников должны совпадать
    """
    
    def __init__(self, client_name: str, reports_dir: Path = Path("reports")):
        self.client_name = client_name
        self.reports_dir = reports_dir / client_name
        self.audit_log: List[AuditResult] = []
    
    def verify_data_source(self, data_point: DataPoint) -> AuditResult:
        """
        Проверяет наличие и достоверность источника данных.
        
        Проверки:
        - Существует ли файл-источник?
        - Есть ли в нем указанная метрика?
        - Совпадает ли значение?
        - Актуальны ли данные (не устарели)?
        """
        issues = []
        evidence = []
        
        # 1. Проверка существования файла
        source_path = self.reports_dir / data_point.source_file
        if not source_path.exists():
            issues.append(f"Source file not found: {data_point.source_file}")
            return AuditResult(
                claim=f"{data_point.metric} = {data_point.value}",
                status="failed",
                evidence=[],
                issues=issues,
                alternative_hypotheses=[],
                confidence=0.0
            )
        
        evidence.append(str(source_path))
        
        # 2. Проверка наличия метрики в файле
        try:
            with open(source_path, 'r') as f:
                source_data = json.load(f)
            
            # Ищем метрику в данных
            metric_found = self._find_metric_in_data(
                source_data, 
                data_point.metric, 
                data_point.period
            )
            
            if not metric_found:
                issues.append(f"Metric '{data_point.metric}' not found in source")
            else:
                # 3. Проверка значения
                if metric_found != data_point.value:
                    issues.append(
                        f"Value mismatch: claimed {data_point.value}, "
                        f"source has {metric_found}"
                    )
        
        except Exception as e:
            issues.append(f"Error reading source: {str(e)}")
        
        # 4. Проверка актуальности данных (не старше 7 дней для динамических отчетов)
        file_age_days = (datetime.now() - datetime.fromtimestamp(source_path.stat().st_mtime)).days
        if file_age_days > 7:
            issues.append(f"Data is {file_age_days} days old - may be stale")
        
        status = "passed" if not issues else "failed"
        confidence = 1.0 if status == "passed" else 0.0
        
        return AuditResult(
            claim=f"{data_point.metric} = {data_point.value} ({data_point.period})",
            status=status,
            evidence=evidence,
            issues=issues,
            alternative_hypotheses=[],
            confidence=confidence
        )
    
    def verify_calculation(
        self, 
        result: float, 
        operands: List[float], 
        operation: str,
        description: str
    ) -> AuditResult:
        """
        Проверяет правильность математических расчетов.
        
        Args:
            result: Заявленный результат
            operands: Операнды
            operation: Тип операции (sum, delta, pct_change, avg, etc)
            description: Описание расчета
        """
        issues = []
        expected = None
        
        if operation == "sum":
            expected = sum(operands)
        elif operation == "delta":
            expected = operands[1] - operands[0]
        elif operation == "pct_change":
            if operands[0] == 0:
                issues.append("Division by zero in percent change")
            else:
                expected = ((operands[1] - operands[0]) / operands[0]) * 100
        elif operation == "avg":
            expected = sum(operands) / len(operands)
        else:
            issues.append(f"Unknown operation: {operation}")
        
        if expected is not None:
            # Допускаем погрешность округления
            if abs(result - expected) > 0.01:
                issues.append(
                    f"Calculation error: expected {expected:.2f}, got {result:.2f}"
                )
        
        status = "passed" if not issues else "failed"
        
        return AuditResult(
            claim=f"{description} = {result}",
            status=status,
            evidence=[f"Operands: {operands}, Operation: {operation}"],
            issues=issues,
            alternative_hypotheses=[],
            confidence=1.0 if status == "passed" else 0.0
        )
    
    def check_hypothesis(
        self, 
        hypothesis: str, 
        supporting_data: List[DataPoint],
        context: Dict[str, Any]
    ) -> AuditResult:
        """
        Проверяет гипотезу на обоснованность и генерирует альтернативы.
        
        Принципы:
        1. Гипотеза должна быть подкреплена данными
        2. Должны быть рассмотрены альтернативные объяснения
        3. Корреляция ≠ причинность
        4. Нужно учитывать сезонность, тренды, внешние факторы
        """
        issues = []
        evidence = []
        alternatives = []
        
        # 1. Проверка наличия данных
        if not supporting_data:
            issues.append("No supporting data for hypothesis")
            return AuditResult(
                claim=hypothesis,
                status="failed",
                evidence=[],
                issues=issues,
                alternative_hypotheses=[],
                confidence=0.0
            )
        
        # 2. Проверка качества данных
        for dp in supporting_data:
            audit = self.verify_data_source(dp)
            if audit.status == "failed":
                issues.extend(audit.issues)
            evidence.extend(audit.evidence)
        
        # 3. Генерация альтернативных гипотез
        alternatives = self._generate_alternative_hypotheses(
            hypothesis, 
            supporting_data, 
            context
        )
        
        # 4. Оценка уверенности
        confidence = self._assess_hypothesis_confidence(
            hypothesis,
            supporting_data,
            alternatives,
            issues
        )
        
        if confidence < 0.5:
            issues.append(f"Low confidence ({confidence:.0%}) - consider alternatives")
        
        status = "passed" if confidence >= 0.7 and not issues else "warning"
        
        return AuditResult(
            claim=hypothesis,
            status=status,
            evidence=evidence,
            issues=issues,
            alternative_hypotheses=alternatives,
            confidence=confidence
        )
    
    def cross_reference(
        self, 
        metric: str, 
        sources: List[Tuple[str, Any]]
    ) -> AuditResult:
        """
        Кросс-проверка одной метрики из разных источников.
        
        Например:
        - Трафик из Метрики vs GSC
        - Конверсии из разных целей
        - Данные за разные периоды
        """
        issues = []
        evidence = [f"{src}: {val}" for src, val in sources]
        
        if len(sources) < 2:
            issues.append("Need at least 2 sources for cross-reference")
        
        # Проверка на расхождения
        values = [val for _, val in sources]
        if len(set(values)) > 1:
            # Разные значения - проверяем допустимое отклонение
            max_val = max(values)
            min_val = min(values)
            deviation = ((max_val - min_val) / min_val) * 100 if min_val != 0 else 100
            
            if deviation > 10:  # Более 10% расхождение
                issues.append(
                    f"Large deviation between sources: {deviation:.1f}% "
                    f"(values: {values})"
                )
        
        status = "passed" if not issues else "warning"
        confidence = 1.0 if status == "passed" else 0.5
        
        return AuditResult(
            claim=f"{metric}: cross-reference check",
            status=status,
            evidence=evidence,
            issues=issues,
            alternative_hypotheses=[],
            confidence=confidence
        )
    
    def audit_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Полный аудит отчета перед публикацией.
        
        Проверяет:
        - Все цифры имеют источники
        - Все расчеты верны
        - Все гипотезы обоснованы
        - Нет противоречий
        """
        self.audit_log = []
        
        # TODO: Реализовать полный аудит структуры отчета
        # Это будет зависеть от формата отчета
        
        summary = {
            "total_checks": len(self.audit_log),
            "passed": len([a for a in self.audit_log if a.status == "passed"]),
            "warnings": len([a for a in self.audit_log if a.status == "warning"]),
            "failed": len([a for a in self.audit_log if a.status == "failed"]),
            "overall_confidence": sum(a.confidence for a in self.audit_log) / len(self.audit_log) if self.audit_log else 0,
            "details": [
                {
                    "claim": a.claim,
                    "status": a.status,
                    "issues": a.issues,
                    "confidence": a.confidence
                }
                for a in self.audit_log if a.status != "passed"
            ]
        }
        
        return summary
    
    def _find_metric_in_data(
        self, 
        data: Dict[str, Any], 
        metric: str, 
        period: str
    ) -> Optional[Any]:
        """Ищет метрику в структуре данных"""
        # Простая реализация - можно расширить
        # TODO: Улучшить поиск по вложенным структурам
        return data.get(metric)
    
    def _generate_alternative_hypotheses(
        self,
        original: str,
        data: List[DataPoint],
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Генерирует альтернативные объяснения для наблюдаемых данных.
        
        Типовые альтернативы:
        - Сезонность
        - Внешние факторы (праздники, новости)
        - Технические проблемы
        - Изменения в tracking
        - Конкуренция
        """
        alternatives = []
        
        # Примеры альтернатив (можно расширить с помощью LLM)
        if "падение" in original.lower() or "снижение" in original.lower():
            alternatives.extend([
                "Сезонное снижение активности",
                "Технические проблемы с tracking",
                "Изменения в методологии измерения",
                "Внешние факторы (экономика, конкуренты)"
            ])
        
        if "рост" in original.lower() or "увеличение" in original.lower():
            alternatives.extend([
                "Сезонный пик активности",
                "Разовая акция/кампания",
                "Изменения в учете данных",
                "Общий рост рынка"
            ])
        
        return alternatives[:3]  # Топ-3 альтернативы
    
    def _assess_hypothesis_confidence(
        self,
        hypothesis: str,
        data: List[DataPoint],
        alternatives: List[str],
        issues: List[str]
    ) -> float:
        """
        Оценивает уверенность в гипотезе (0-1).
        
        Факторы:
        - Количество и качество данных
        - Наличие альтернатив
        - Найденные проблемы
        """
        confidence = 0.5  # Базовая
        
        # +0.1 за каждую точку данных (макс +0.3)
        confidence += min(len(data) * 0.1, 0.3)
        
        # -0.1 за каждую найденную проблему
        confidence -= len(issues) * 0.1
        
        # -0.05 за каждую равновероятную альтернативу
        confidence -= len(alternatives) * 0.05
        
        return max(0.0, min(1.0, confidence))


def create_audit_checklist(analysis_type: str) -> List[str]:
    """
    Создает чеклист проверок для конкретного типа анализа.
    
    Args:
        analysis_type: Тип анализа (traffic, conversion, seo, etc)
    
    Returns:
        Список вопросов для проверки
    """
    checklists = {
        "traffic": [
            "Все источники трафика имеют данные из Метрики?",
            "Сумма источников = общий трафик?",
            "Нет ли аномальных скачков (>300%)?",
            "Учтена ли сезонность?",
            "Проверены ли данные за предыдущие периоды?",
        ],
        "conversion": [
            "Все цели настроены в Метрике?",
            "CR не превышает разумные пределы (<10%)?",
            "Количество конверсий <= количество визитов?",
            "Есть ли данные по всем источникам?",
            "Проверена ли корректность tracking?",
        ],
        "seo": [
            "Данные взяты из GSC или Вебмастера?",
            "Период совпадает с анализом трафика?",
            "Проверены ли позиции ключевых запросов?",
            "Нет ли дублей запросов?",
            "Учтены ли брендовые vs небрендовые?",
        ],
        "hypothesis": [
            "Гипотеза подкреплена минимум 3 точками данных?",
            "Рассмотрены ли альтернативные объяснения?",
            "Учтены ли внешние факторы?",
            "Можно ли проверить гипотезу A/B тестом?",
            "Указана уверенность в гипотезе?",
        ]
    }
    
    return checklists.get(analysis_type, [])

