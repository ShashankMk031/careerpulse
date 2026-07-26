from backend.app.models.entities import SalaryAnalytics
from backend.app.utils.context import track_db_time

class SalaryRepository:
    @staticmethod
    @track_db_time
    def get_salary_tiers(conn) -> list[SalaryAnalytics]:
        """
        Retrieves all salary tier records ordered by salary ranges where possible.
        """
        query = """
            SELECT salary_tier, jobs_count, avg_salary_min, avg_salary_max, created_at, updated_at
            FROM serving.salary_analytics
            ORDER BY avg_salary_min ASC NULLS LAST;
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                SalaryAnalytics(
                    salary_tier=row[0],
                    jobs_count=row[1],
                    avg_salary_min=row[2],
                    avg_salary_max=row[3],
                    created_at=row[4],
                    updated_at=row[5]
                )
                for row in rows
            ]
