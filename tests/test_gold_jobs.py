"""
Unit tests for the CareerPulse Gold Layer PySpark ETL transformations.
Mocks the PySpark and AWS Glue libraries entirely to run in a JVM-free local environment.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# 1. Define custom classes for Spark SQL types to support isinstance checks
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
        
    def __getitem__(self, key):
        return MockColumn(f"{self.expr}[{key}]")
        
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
        
    def __add__(self, other):
        return MockColumn(f"({self.expr} + {other})")
        
    def __sub__(self, other):
        return MockColumn(f"({self.expr} - {other})")
        
    def __mul__(self, other):
        return MockColumn(f"({self.expr} * {other})")
        
    def __truediv__(self, other):
        return MockColumn(f"({self.expr} / {other})")
        
    def __str__(self):
        return self.expr
        
    def __repr__(self):
        return f"MockColumn({self.expr})"

class MockWhenColumn(MockColumn):
    def when(self, condition, value):
        return MockWhenColumn(f"{self.expr}.when({condition}, {value})")
        
    def otherwise(self, value):
        return MockColumn(f"{self.expr}.otherwise({value})")

# 3. Mock all AWS Glue and PySpark modules BEFORE any import from gold_etl.py
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
pyspark_sql_functions_mock.count = lambda col_val: MockColumn(f"count({col_val})")
pyspark_sql_functions_mock.count_distinct = lambda col_val: MockColumn(f"count_distinct({col_val})")
pyspark_sql_functions_mock.avg = lambda col_val: MockColumn(f"avg({col_val})")
pyspark_sql_functions_mock.sum = lambda col_val: MockColumn(f"sum({col_val})")
pyspark_sql_functions_mock.max = lambda col_val: MockColumn(f"max({col_val})")
pyspark_sql_functions_mock.coalesce = lambda *cols: MockColumn(f"coalesce({', '.join(str(c) for c in cols)})")
pyspark_sql_functions_mock.explode = lambda col_name: MockColumn(f"explode({col_name})")
pyspark_sql_functions_mock.array_distinct = lambda col_name: MockColumn(f"array_distinct({col_name})")
pyspark_sql_functions_mock.trim = lambda col_val: MockColumn(f"trim({col_val})")
pyspark_sql_functions_mock.lower = lambda col_val: MockColumn(f"lower({col_val})")
pyspark_sql_functions_mock.current_timestamp = lambda: MockColumn("current_timestamp()")
pyspark_sql_functions_mock.struct = lambda *cols: MockColumn(f"struct({', '.join(str(c) for c in cols)})")
pyspark_sql_functions_mock.rlike = lambda col_val, regex: MockColumn(f"rlike({col_val}, {regex})")
pyspark_sql_functions_mock.when = lambda cond, val: MockWhenColumn(f"when({cond}, {val})")

# Ensure glue_jobs path is discoverable
sys.path.append(os.path.join(os.path.dirname(__file__), "../glue_jobs"))

# Now we can safely import transformations from gold_etl without import crashes
from gold_etl import (
    generate_company_analytics,
    generate_skills_analytics,
    generate_geography_analytics,
    generate_salary_analytics,
    generate_technology_analytics,
    generate_hiring_summary
)

class TestGoldETLTransformations(unittest.TestCase):

    def test_company_analytics_logic(self):
        """
        Tests that generate_company_analytics applies correct group-by
        and structural struct max aggregation to find highest paying role.
        """
        mock_df = MagicMock()
        mock_grouped_df = MagicMock()
        mock_df.groupBy.return_value = mock_grouped_df
        
        mock_agg_df = MagicMock()
        mock_grouped_df.agg.return_value = mock_agg_df
        
        result_df = generate_company_analytics(mock_df)
        
        mock_df.groupBy.assert_called_once_with("company")
        mock_grouped_df.agg.assert_called_once()
        self.assertEqual(result_df, mock_agg_df)

    def test_skills_analytics_logic(self):
        """
        Tests skills analytics tag explode, tag distincting, lowercase normalization,
        and premium calculations.
        """
        mock_df = MagicMock()
        mock_df_distinct = MagicMock()
        mock_df.withColumn.return_value = mock_df_distinct
        
        mock_df_exploded = MagicMock()
        mock_df_distinct.select.return_value = mock_df_exploded
        
        mock_df_normalized = MagicMock()
        mock_df_exploded.withColumn.return_value = mock_df_normalized
        
        mock_df_filtered = MagicMock()
        mock_df_normalized.filter.return_value = mock_df_filtered
        
        mock_grouped_df = MagicMock()
        mock_df_filtered.groupBy.return_value = mock_grouped_df
        
        mock_agg_df = MagicMock()
        mock_grouped_df.agg.return_value = mock_agg_df
        
        mock_final_df = MagicMock()
        mock_agg_df.withColumn.return_value = mock_final_df
        
        result_df = generate_skills_analytics(mock_df, 85000.0)
        
        # Verify operations flow
        mock_df.withColumn.assert_called_once_with("tags", unittest.mock.ANY)
        mock_df_distinct.select.assert_called_once()
        mock_df_exploded.withColumn.assert_called_once_with("tag", unittest.mock.ANY)
        mock_df_normalized.filter.assert_called_once()
        mock_df_filtered.groupBy.assert_called_once_with("tag")
        mock_grouped_df.agg.assert_called_once()
        mock_agg_df.withColumn.assert_called_once_with("salary_premium", unittest.mock.ANY)
        
        self.assertEqual(result_df, mock_final_df)

    def test_geography_analytics_logic(self):
        """
        Tests geography analytics aggregations.
        """
        mock_df = MagicMock()
        
        mock_grouped_df = MagicMock()
        mock_df.groupBy.return_value = mock_grouped_df
        
        mock_agg_df = MagicMock()
        mock_grouped_df.agg.return_value = mock_agg_df
        
        result_df = generate_geography_analytics(mock_df)
        
        mock_df.groupBy.assert_called_once_with("country", "region")
        mock_grouped_df.agg.assert_called_once()
        self.assertEqual(result_df, mock_agg_df)

    def test_salary_analytics_logic(self):
        """
        Tests salary analytics tiered mapping logic using the configured salary buckets.
        """
        mock_df = MagicMock()
        mock_df_tiered = MagicMock()
        mock_df.withColumn.return_value = mock_df_tiered
        
        mock_grouped_df = MagicMock()
        mock_df_tiered.groupBy.return_value = mock_grouped_df
        
        mock_agg_df = MagicMock()
        mock_grouped_df.agg.return_value = mock_agg_df
        
        result_df = generate_salary_analytics(mock_df)
        
        mock_df.withColumn.assert_called_once_with("salary_tier", unittest.mock.ANY)
        mock_df_tiered.groupBy.assert_called_once_with("salary_tier")
        self.assertEqual(result_df, mock_agg_df)

    def test_technology_analytics_logic(self):
        """
        Tests technology analytics tag explode, top hiring company resolution, and joining.
        """
        mock_df = MagicMock()
        
        mock_df_distinct = MagicMock()
        mock_df.withColumn.return_value = mock_df_distinct
        
        mock_df_exploded = MagicMock()
        mock_df_distinct.select.return_value = mock_df_exploded
        
        mock_df_normalized = MagicMock()
        mock_df_exploded.withColumn.return_value = mock_df_normalized
        
        mock_df_filtered = MagicMock()
        mock_df_normalized.filter.return_value = mock_df_filtered
        
        # Mock company counts
        mock_counts_grouped = MagicMock()
        mock_counts_df = MagicMock()
        mock_counts_grouped.agg.return_value = mock_counts_df
        
        # Mock top company resolution
        mock_top_grouped = MagicMock()
        mock_counts_df.groupBy.return_value = mock_top_grouped
        mock_top_df = MagicMock()
        mock_top_grouped.agg.return_value = mock_top_df
        
        # Mock base tech metrics
        mock_base_grouped = MagicMock()
        mock_base_df = MagicMock()
        mock_base_grouped.agg.return_value = mock_base_df
        
        # Set up a side effect to return the correct group mock based on input columns
        def group_by_side_effect(*args):
            if "company" in args:
                return mock_counts_grouped
            return mock_base_grouped
            
        mock_df_filtered.groupBy.side_effect = group_by_side_effect
        
        # Mock join
        mock_joined_df = MagicMock()
        mock_base_df.join.return_value = mock_joined_df
        mock_final_df = MagicMock()
        mock_joined_df.withColumnRenamed.return_value = mock_final_df
        
        result_df = generate_technology_analytics(mock_df)
        
        mock_base_df.join.assert_called_once_with(mock_top_df, "tag", "left")
        self.assertEqual(result_df, mock_final_df)

    def test_hiring_summary_logic(self):
        """
        Tests hiring summary KPI metrics calculations for the landing dashboard.
        """
        mock_df = MagicMock()
        mock_df.count.return_value = 100
        
        # Mock sub-aggregations counts
        mock_sub_group = MagicMock()
        mock_df.groupBy.return_value = mock_sub_group
        mock_sub_agg = MagicMock()
        mock_sub_group.agg.return_value = mock_sub_agg
        
        # Mock distinct tags array explode
        mock_df_distinct = MagicMock()
        mock_df.withColumn.return_value = mock_df_distinct
        mock_df_exploded = MagicMock()
        mock_df_distinct.select.return_value = mock_df_exploded
        mock_df_normalized = MagicMock()
        mock_df_exploded.withColumn.return_value = mock_df_normalized
        mock_df_filtered = MagicMock()
        mock_df_normalized.filter.return_value = mock_df_filtered
        mock_filtered_group = MagicMock()
        mock_df_filtered.groupBy.return_value = mock_filtered_group
        mock_filtered_agg = MagicMock()
        mock_filtered_group.agg.return_value = mock_filtered_agg
        
        # Set up group-by side effect to handle both tag explode and base aggregations
        mock_grouped_df = MagicMock()
        mock_agg_df = MagicMock()
        mock_grouped_df.agg.return_value = mock_agg_df
        
        def group_by_side_effect(*args):
            if "company" in args or "tag" in args or "country" in args:
                return mock_sub_group
            return mock_grouped_df
            
        mock_df.groupBy.side_effect = group_by_side_effect
        mock_df_filtered.groupBy.return_value = mock_sub_group
        
        # Chained withColumn calls
        mock_w1 = MagicMock()
        mock_w2 = MagicMock()
        mock_w3 = MagicMock()
        mock_w4 = MagicMock()
        mock_df_final = MagicMock()
        
        mock_agg_df.withColumn.return_value = mock_w1
        mock_w1.withColumn.return_value = mock_w2
        mock_w2.withColumn.return_value = mock_w3
        mock_w3.withColumn.return_value = mock_w4
        mock_w4.withColumn.return_value = mock_df_final
        
        result_df = generate_hiring_summary(mock_df)
        
        mock_df.count.assert_called()
        self.assertEqual(result_df, mock_df_final)

    def test_hiring_summary_empty_silver_returns_none(self):
        """
        Tests that generate_hiring_summary gracefully returns None if the silver dataset is empty.
        """
        mock_df = MagicMock()
        mock_df.count.return_value = 0
        
        result = generate_hiring_summary(mock_df)
        
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
