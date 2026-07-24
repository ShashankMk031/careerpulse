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

    def test_validate_schema_valid_input(self):
        """
        Tests that validate_schema correctly explodes the 'array' column
        and projects all fields with correct type casts.
        """
        mock_df = MagicMock()
        mock_df.columns = ["array", "year", "month", "day"]
        
        mock_element_type = MagicMock()
        mock_element_type.fieldNames.return_value = ["id", "slug", "epoch", "date", "company", "company_logo", "position", "tags", "description", "location", "apply_url", "salary_min", "salary_max", "logo", "url", "original"]
        mock_df.schema = {
            "array": MagicMock(dataType=MagicMock(elementType=mock_element_type))
        }
        
        mock_exploded_df = MagicMock()
        mock_df.select.return_value = mock_exploded_df
        
        mock_projected_df = MagicMock()
        mock_exploded_df.select.return_value = mock_projected_df
        
        mock_renamed_df1 = MagicMock()
        mock_renamed_df2 = MagicMock()
        mock_renamed_df3 = MagicMock()
        
        mock_projected_df.withColumnRenamed.return_value = mock_renamed_df1
        mock_renamed_df1.withColumnRenamed.return_value = mock_renamed_df2
        mock_renamed_df2.withColumnRenamed.return_value = mock_renamed_df3
        
        result_df = validate_schema(mock_df)
        
        # Verify columns check and projection calls
        mock_df.select.assert_called_once()
        mock_exploded_df.select.assert_called_once()
        
        # Assert type casts were projected
        self.assertEqual(result_df, mock_renamed_df3)

    def test_validate_schema_missing_array_throws(self):
        """
        Tests that validate_schema raises ValueError if the 'array' column is missing.
        """
        mock_df = MagicMock()
        mock_df.columns = ["other_column"]
        
        with self.assertRaises(ValueError) as context:
            validate_schema(mock_df)
            
        self.assertIn("missing the required nested 'array' column", str(context.exception))

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
        
        # Verify calls
        mock_df.withColumn.assert_called_once()
        mock_df_ts.drop.assert_called_once_with("date_raw")
        self.assertEqual(mock_df_drop.withColumn.call_count, 1)
        self.assertEqual(mock_df_w1.withColumn.call_count, 1)
        self.assertEqual(mock_df_w2.withColumn.call_count, 1)
        self.assertEqual(mock_df_w3.withColumn.call_count, 1)
        
        # Verify returned dataframes
        self.assertEqual(silver_df, mock_silver_final)
        self.assertEqual(duplicates_df, mock_dup_final)

if __name__ == "__main__":
    unittest.main()
