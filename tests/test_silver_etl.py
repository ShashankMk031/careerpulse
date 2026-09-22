"""
Unit tests for the CareerPulse Silver Layer PySpark ETL transformations.
Mocks the PySpark and AWS Glue libraries entirely to run in a JVM-free local environment.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

# 1. Define custom classes for Spark SQL types to support native isinstance() checks
class StringType:
    pass

class LongType:
    pass

class IntegerType:
    pass

class BooleanType:
    pass

class TimestampType:
    pass

class ArrayType:
    def __init__(self, elementType):
        self.elementType = elementType

# 2. Define a Mock Column class to support chaining Spark expressions
class MockColumn:
    def __init__(self, expr="column"):
        self.expr = expr
        
    def alias(self, name):
        return MockColumn(f"{self.expr}.alias({name})")
        
    def cast(self, dataType):
        return MockColumn(f"cast({self.expr} as {dataType})")
        
    def isNull(self):
        return MockColumn(f"{self.expr} is null")
        
    def isNotNull(self):
        return MockColumn(f"{self.expr} is not null")
        
    def rlike(self, pattern):
        return MockColumn(f"{self.expr}.rlike({pattern})")
        
    def over(self, windowSpec):
        return MockColumn(f"{self.expr} over {windowSpec}")
        
    def __or__(self, other):
        return MockColumn(f"({self.expr} or {other})")
        
    def __and__(self, other):
        return MockColumn(f"({self.expr} and {other})")
        
    def __eq__(self, other):
        return MockColumn(f"({self.expr} == {other})")
        
    def __ne__(self, other):
        return MockColumn(f"({self.expr} != {other})")
        
    def __lt__(self, other):
        return MockColumn(f"({self.expr} < {other})")
        
    def __gt__(self, other):
        return MockColumn(f"({self.expr} > {other})")
        
    def __ge__(self, other):
        return MockColumn(f"({self.expr} >= {other})")
        
    def __le__(self, other):
        return MockColumn(f"({self.expr} <= {other})")
        
    def __str__(self):
        return self.expr
        
    def __repr__(self):
        return f"MockColumn({self.expr})"

class MockWhenColumn(MockColumn):
    def when(self, condition, value):
        return MockWhenColumn(f"{self.expr}.when({condition}, {value})")
        
    def otherwise(self, value):
        return MockColumn(f"{self.expr}.otherwise({value})")

# 3. Mock all AWS Glue and PySpark modules BEFORE any import from silver_etl.py
sys.modules['awsglue'] = MagicMock()
sys.modules['awsglue.utils'] = MagicMock()
sys.modules['awsglue.context'] = MagicMock()
sys.modules['awsglue.job'] = MagicMock()

pyspark_mock = MagicMock()
sys.modules['pyspark'] = pyspark_mock
sys.modules['pyspark.context'] = MagicMock()

pyspark_sql_mock = MagicMock()
sys.modules['pyspark.sql'] = pyspark_sql_mock

# Mock PySpark types
pyspark_sql_types_mock = MagicMock()
sys.modules['pyspark.sql.types'] = pyspark_sql_types_mock

pyspark_sql_types_mock.StructType = lambda fields: fields
pyspark_sql_types_mock.StructField = lambda name, type_obj, nullable=True: (name, type_obj)
pyspark_sql_types_mock.StringType = StringType
pyspark_sql_types_mock.LongType = LongType
pyspark_sql_types_mock.IntegerType = IntegerType
pyspark_sql_types_mock.BooleanType = BooleanType
pyspark_sql_types_mock.TimestampType = TimestampType
pyspark_sql_types_mock.ArrayType = ArrayType

# Mock PySpark functions
pyspark_sql_functions_mock = MagicMock()
sys.modules['pyspark.sql.functions'] = pyspark_sql_functions_mock

# Map functions to return MockColumn expressions
pyspark_sql_functions_mock.col = lambda name: MockColumn(f"col({name})")
pyspark_sql_functions_mock.lit = lambda val: MockColumn(f"lit({val})")
pyspark_sql_functions_mock.explode = lambda col_name: MockColumn(f"explode({col_name})")
pyspark_sql_functions_mock.trim = lambda col_val: MockColumn(f"trim({col_val})")
pyspark_sql_functions_mock.lower = lambda col_val: MockColumn(f"lower({col_val})")
pyspark_sql_functions_mock.to_timestamp = lambda col_val, fmt: MockColumn(f"to_timestamp({col_val}, {fmt})")
pyspark_sql_functions_mock.row_number = lambda: MockColumn("row_number()")
pyspark_sql_functions_mock.desc = lambda name: MockColumn(f"desc({name})")
pyspark_sql_functions_mock.when = lambda cond, val: MockWhenColumn(f"when({cond}, {val})")

# Mock PySpark window functions
pyspark_sql_window_mock = MagicMock()
sys.modules['pyspark.sql.window'] = pyspark_sql_window_mock

# Ensure glue_jobs path is discoverable
sys.path.append(os.path.join(os.path.dirname(__file__), "../glue_jobs"))

# Now we can safely import transformations from silver_etl without import crashes
# pyrefly: ignore [missing-import]
from silver_etl import validate_schema, validate_business_rules, clean_dataframe, transform_dataframe

class TestSilverETLTransformations(unittest.TestCase):

    def setUp(self):
        pyspark_sql_window_mock.reset_mock()

    def test_validate_schema_valid_flat_bronze_input(self):
        """
        Tests that validate_schema accepts the flat Bronze schema
        and projects all fields with correct type casts and column mapping.
        """
        mock_df = MagicMock()
        mock_df.columns = [
            "id", "slug", "epoch", "date", "company", "company_logo",
            "position", "tags", "description", "location", "apply_url",
            "salary_min", "salary_max", "logo", "url", "original",
            "year", "month", "day"
        ]
        
        mock_projected_df = MagicMock()
        mock_df.select.return_value = mock_projected_df
        
        mock_renamed_df1 = MagicMock()
        mock_renamed_df2 = MagicMock()
        mock_renamed_df3 = MagicMock()
        
        mock_projected_df.withColumnRenamed.return_value = mock_renamed_df1
        mock_renamed_df1.withColumnRenamed.return_value = mock_renamed_df2
        mock_renamed_df2.withColumnRenamed.return_value = mock_renamed_df3
        
        result_df = validate_schema(mock_df)
        
        # Verify select called once on flat Bronze DataFrame
        mock_df.select.assert_called_once()
        
        # Verify projected expressions
        select_args = mock_df.select.call_args[0]
        select_exprs = [str(arg) for arg in select_args]
        
        # 1. Verify id is cast to LongType
        id_expr = next(expr for expr in select_exprs if ".alias(id)" in expr)
        self.assertIn("cast(col(id) as", id_expr)
        self.assertIn("LongType", id_expr)
        
        # 2. Verify epoch is cast to LongType
        epoch_expr = next(expr for expr in select_exprs if ".alias(epoch)" in expr)
        self.assertIn("cast(col(epoch) as", epoch_expr)
        self.assertIn("LongType", epoch_expr)
        
        # 3. Verify date becomes date_raw
        date_expr = next(expr for expr in select_exprs if ".alias(date_raw)" in expr)
        self.assertIn("cast(col(date) as", date_expr)
        self.assertIn("StringType", date_expr)
        
        # 4. Verify salary fields are correctly typed
        salary_min_expr = next(expr for expr in select_exprs if ".alias(salary_min)" in expr)
        self.assertIn("cast(col(salary_min) as", salary_min_expr)
        self.assertIn("IntegerType", salary_min_expr)
        
        salary_max_expr = next(expr for expr in select_exprs if ".alias(salary_max)" in expr)
        self.assertIn("cast(col(salary_max) as", salary_max_expr)
        self.assertIn("IntegerType", salary_max_expr)
        
        # 5. Verify tags preserved as ArrayType
        tags_expr = next(expr for expr in select_exprs if ".alias(tags)" in expr)
        self.assertIn("ArrayType", tags_expr)
        
        # 6. Verify partition column renaming
        self.assertEqual(result_df, mock_renamed_df3)
        mock_projected_df.withColumnRenamed.assert_called_with("yearProjected", "year")
        mock_renamed_df1.withColumnRenamed.assert_called_with("monthProjected", "month")
        mock_renamed_df2.withColumnRenamed.assert_called_with("dayProjected", "day")

    def test_validate_schema_missing_columns_throws(self):
        """
        Tests that validate_schema raises ValueError if required Bronze columns are missing.
        """
        mock_df = MagicMock()
        mock_df.columns = ["id", "company", "position"]  # missing required columns like epoch, date, etc.
        
        with self.assertRaises(ValueError) as context:
            validate_schema(mock_df)
            
        self.assertIn("missing required Bronze columns", str(context.exception))

    def test_validate_business_rules_logic(self):
        """
        Tests that validate_business_rules applies rule expressions to tag records.
        """
        mock_df = MagicMock()
        mock_with_column_df = MagicMock()
        mock_df.withColumn.return_value = mock_with_column_df
        
        result_df = validate_business_rules(mock_df)
        
        # Assert Spark DataFrame operations
        mock_df.withColumn.assert_called_once()
        self.assertEqual(result_df, mock_with_column_df)

    def test_clean_dataframe_trims_strings(self):
        """
        Tests that clean_dataframe identifies StringType columns and applies trim().
        """
        # Create mock fields with native type classes
        mock_field_1 = MagicMock()
        mock_field_1.name = "company"
        mock_field_1.dataType = StringType()
        
        mock_field_2 = MagicMock()
        mock_field_2.name = "salary_min"
        mock_field_2.dataType = IntegerType()
        
        mock_field_3 = MagicMock()
        mock_field_3.name = "reason"
        mock_field_3.dataType = StringType()
        
        mock_schema = MagicMock()
        mock_schema.fields = [mock_field_1, mock_field_2, mock_field_3]
        
        mock_df = MagicMock()
        mock_df.schema = mock_schema
        
        mock_df_trimmed = MagicMock()
        mock_df.withColumn.return_value = mock_df_trimmed
        
        result_df = clean_dataframe(mock_df)
        
        # Verify withColumn was called for 'company' string column (and skipped 'reason')
        mock_df.withColumn.assert_called_once()
        self.assertEqual(result_df, mock_df_trimmed)

    def test_transform_dataframe_flow(self):
        """
        Tests that transform_dataframe adds timestamp columns, ranks rows by epoch,
        and returns deduplicated silver and duplicate quarantine datasets.
        """
        mock_df = MagicMock()
        
        mock_df_ts = MagicMock()
        mock_df.withColumn.return_value = mock_df_ts
        
        mock_df_drop = MagicMock()
        mock_df_ts.drop.return_value = mock_df_drop
        
        mock_df_w1 = MagicMock()
        mock_df_w2 = MagicMock()
        mock_df_w3 = MagicMock()
        
        mock_df_drop.withColumn.return_value = mock_df_w1
        mock_df_w1.withColumn.return_value = mock_df_w2
        mock_df_w2.withColumn.return_value = mock_df_w3
        
        mock_df_ranked = MagicMock()
        mock_df_w3.withColumn.return_value = mock_df_ranked
        
        # Setup mock filtering results
        mock_silver_filtered = MagicMock()
        mock_silver_final = MagicMock()
        
        mock_dup_filtered = MagicMock()
        mock_dup_with_reason = MagicMock()
        mock_dup_final = MagicMock()
        
        # Configure filters based on filter condition
        mock_df_ranked.filter.side_effect = lambda expr: (
            mock_silver_filtered if "== 1" in str(expr) else mock_dup_filtered
        )
        
        mock_silver_filtered.drop.return_value = mock_silver_final
        
        mock_dup_filtered.withColumn.return_value = mock_dup_with_reason
        mock_dup_with_reason.drop.return_value = mock_dup_final
        
        silver_df, duplicates_df = transform_dataframe(mock_df)
        
        # Verify date_raw was parsed into date_posted with the ISO-8601 format and dropped
        mock_df.withColumn.assert_called_once()
        self.assertEqual(mock_df.withColumn.call_args[0][0], "date_posted")
        self.assertIn("to_timestamp(col(date_raw)", str(mock_df.withColumn.call_args[0][1]))
        self.assertIn("yyyy-MM-dd'T'HH:mm:ssXXX", str(mock_df.withColumn.call_args[0][1]))
        mock_df_ts.drop.assert_called_once_with("date_raw")
        
        # Verify deduplication window partitioned by id and ordered by snapshot date (year, month, day) then epoch descending
        pyspark_sql_window_mock.Window.partitionBy.assert_called_with("id")
        pyspark_sql_window_mock.Window.partitionBy.return_value.orderBy.assert_called_once()
        order_call_args = pyspark_sql_window_mock.Window.partitionBy.return_value.orderBy.call_args[0]
        order_exprs = [str(arg) for arg in order_call_args]
        self.assertEqual(len(order_exprs), 4)
        self.assertIn("desc(year)", order_exprs[0])
        self.assertIn("desc(month)", order_exprs[1])
        self.assertIn("desc(day)", order_exprs[2])
        self.assertIn("desc(epoch)", order_exprs[3])
        
        # Verify duplicate records receive reason="duplicate"
        mock_dup_filtered.withColumn.assert_called_once_with("reason", mock_dup_filtered.withColumn.call_args[0][1])
        self.assertIn("duplicate", str(mock_dup_filtered.withColumn.call_args[0][1]))
        
        self.assertEqual(mock_df_drop.withColumn.call_count, 1)
        self.assertEqual(mock_df_w1.withColumn.call_count, 1)
        self.assertEqual(mock_df_w2.withColumn.call_count, 1)
        self.assertEqual(mock_df_w3.withColumn.call_count, 1)
        
        # Verify returned dataframes
        self.assertEqual(silver_df, mock_silver_final)
        self.assertEqual(duplicates_df, mock_dup_final)

    def test_deduplication_identical_epoch_newest_snapshot_wins(self):
        """
        Regression test for bug where identical epoch between snapshots had no deterministic tie-breaker.
        id = "123", 09/18: epoch = 1000, 09/19: epoch = 1000.
        Verify that the 09/19 record survives deduplication into Silver, and 09/18 is quarantined.
        """
        rows = [
            {"id": "123", "epoch": 1000, "year": "2026", "month": "09", "day": "18", "location": "Remote", "date_raw": "2026-09-18T10:00:00Z"},
            {"id": "123", "epoch": 1000, "year": "2026", "month": "09", "day": "19", "location": "Remote", "date_raw": "2026-09-19T10:00:00Z"},
        ]
        df = MockDataFrameWithRows(rows)
        silver_df, duplicates_df = transform_dataframe(df)
        
        silver_records = silver_df.collect()
        duplicate_records = duplicates_df.collect()
        
        self.assertEqual(len(silver_records), 1)
        self.assertEqual(silver_records[0]["day"], "19")
        self.assertEqual(silver_records[0]["epoch"], 1000)
        
        self.assertEqual(len(duplicate_records), 1)
        self.assertEqual(duplicate_records[0]["day"], "18")
        self.assertEqual(duplicate_records[0]["reason"], "duplicate")

    def test_deduplication_older_snapshot_higher_epoch_snapshot_date_wins(self):
        """
        Verify that snapshot/ingestion date is the primary ordering criterion:
        id = "123", 09/18: epoch = 2000, 09/19: epoch = 1000.
        Verify that 09/19 still wins because snapshot date takes precedence over source epoch.
        """
        rows = [
            {"id": "123", "epoch": 2000, "year": "2026", "month": "09", "day": "18", "location": "Remote", "date_raw": "2026-09-18T10:00:00Z"},
            {"id": "123", "epoch": 1000, "year": "2026", "month": "09", "day": "19", "location": "Remote", "date_raw": "2026-09-19T10:00:00Z"},
        ]
        df = MockDataFrameWithRows(rows)
        silver_df, duplicates_df = transform_dataframe(df)
        
        silver_records = silver_df.collect()
        duplicate_records = duplicates_df.collect()
        
        self.assertEqual(len(silver_records), 1)
        self.assertEqual(silver_records[0]["day"], "19")
        self.assertEqual(silver_records[0]["epoch"], 1000)
        
        self.assertEqual(len(duplicate_records), 1)
        self.assertEqual(duplicate_records[0]["day"], "18")
        self.assertEqual(duplicate_records[0]["reason"], "duplicate")

    def test_deduplication_normal_case_newest_snapshot_wins(self):
        """
        Normal case where newer snapshot also has newer epoch:
        id = "123", 09/18: epoch = 1000, 09/19: epoch = 2000.
        Verify that 09/19 wins.
        """
        rows = [
            {"id": "123", "epoch": 1000, "year": "2026", "month": "09", "day": "18", "location": "Remote", "date_raw": "2026-09-18T10:00:00Z"},
            {"id": "123", "epoch": 2000, "year": "2026", "month": "09", "day": "19", "location": "Remote", "date_raw": "2026-09-19T10:00:00Z"},
        ]
        df = MockDataFrameWithRows(rows)
        silver_df, duplicates_df = transform_dataframe(df)
        
        silver_records = silver_df.collect()
        duplicate_records = duplicates_df.collect()
        
        self.assertEqual(len(silver_records), 1)
        self.assertEqual(silver_records[0]["day"], "19")
        self.assertEqual(silver_records[0]["epoch"], 2000)
        
        self.assertEqual(len(duplicate_records), 1)
        self.assertEqual(duplicate_records[0]["day"], "18")
        self.assertEqual(duplicate_records[0]["reason"], "duplicate")


    def test_deduplication_window_specification_contract(self):
        """
        Directly asserts that transform_dataframe configures the Window specification
        with the exact expected partition and hierarchical descending sort columns:
        Window.partitionBy('id').orderBy(desc('year'), desc('month'), desc('day'), desc('epoch'))
        """
        mock_df = MagicMock()
        transform_dataframe(mock_df)

        # 1. Assert partition column is strictly 'id'
        pyspark_sql_window_mock.Window.partitionBy.assert_called_with("id")

        # 2. Assert orderBy was called
        pyspark_sql_window_mock.Window.partitionBy.return_value.orderBy.assert_called_once()
        order_call_args = pyspark_sql_window_mock.Window.partitionBy.return_value.orderBy.call_args[0]
        order_exprs = [str(arg) for arg in order_call_args]

        # 3. Assert exact count and hierarchical ordering: year -> month -> day -> epoch
        self.assertEqual(len(order_exprs), 4)
        self.assertEqual(order_exprs[0], "desc(year)")
        self.assertEqual(order_exprs[1], "desc(month)")
        self.assertEqual(order_exprs[2], "desc(day)")
        self.assertEqual(order_exprs[3], "desc(epoch)")


class Row(dict):
    """Mock Spark Row supporting key access and attribute access."""
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)


class MockDataFrameWithRows:
    """
    Lightweight simulation DataFrame for unit testing PySpark pipeline flow in a JVM-free environment.
    Note: In local test runs without a Java Runtime (JVM), PySpark cannot start a local SparkSession.
    This mock reads the actual window specification AST produced by production code and simulates
    how row_number(), filtering, and quarantine tagging consume that window specification.
    """
    def __init__(self, rows):
        self.rows = [Row(r) for r in rows]

    def withColumn(self, col_name, expr):
        if col_name == "row_num":
            # Extract ordering from windowSpec orderBy call on mock
            order_call_args = pyspark_sql_window_mock.Window.partitionBy.return_value.orderBy.call_args
            order_exprs = [str(arg) for arg in order_call_args[0]] if order_call_args else []
            
            # Group rows by partition column ('id')
            from collections import defaultdict
            groups = defaultdict(list)
            for r in self.rows:
                groups[r.get("id")].append(Row(r))
            
            new_rows = []
            for job_id, group in groups.items():
                def sort_key(row):
                    key = []
                    for o in order_exprs:
                        if "desc(year)" in o:
                            key.append(str(row.get("year", "")))
                        elif "desc(month)" in o:
                            key.append(str(row.get("month", "")))
                        elif "desc(day)" in o:
                            key.append(str(row.get("day", "")))
                        elif "desc(epoch)" in o:
                            key.append(int(row.get("epoch", 0)))
                    return tuple(key)
                
                group.sort(key=sort_key, reverse=True)
                for rank, row in enumerate(group, start=1):
                    row["row_num"] = rank
                    new_rows.append(row)
            return MockDataFrameWithRows(new_rows)
        elif col_name == "reason":
            new_rows = []
            for r in self.rows:
                r_copy = Row(r)
                r_copy["reason"] = "duplicate" if "duplicate" in str(expr) else str(expr)
                new_rows.append(r_copy)
            return MockDataFrameWithRows(new_rows)
        else:
            new_rows = [Row(r) for r in self.rows]
            return MockDataFrameWithRows(new_rows)

    def drop(self, col_name):
        new_rows = []
        for r in self.rows:
            r_copy = Row(r)
            r_copy.pop(col_name, None)
            new_rows.append(r_copy)
        return MockDataFrameWithRows(new_rows)

    def filter(self, expr):
        expr_str = str(expr)
        if "== 1" in expr_str:
            filtered = [r for r in self.rows if r.get("row_num") == 1]
        elif "> 1" in expr_str:
            filtered = [r for r in self.rows if r.get("row_num", 0) > 1]
        else:
            filtered = list(self.rows)
        return MockDataFrameWithRows(filtered)

    def collect(self):
        return list(self.rows)

    def count(self):
        return len(self.rows)

if __name__ == "__main__":
    unittest.main()
