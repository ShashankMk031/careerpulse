from backend.app.models.entities import HiringSummary, DatasetFreshness
from backend.app.utils.context import track_db_time

class SummaryRepository:
    @staticmethod
    @track_db_time
    def get_kpis(conn) -> HiringSummary | None:
        """
        Retrieves the latest execution dashboard summary record.
        """
        query = """
            SELECT id, total_jobs, total_companies, total_locations, remote_jobs, remote_percentage,
                   average_salary, median_salary, highest_salary, highest_paying_company,
                   top_company, top_skill, top_country, jobs_with_salary, jobs_without_salary,
                   generation_timestamp, created_at, updated_at
            FROM serving.hiring_summary
            ORDER BY generation_timestamp DESC
            LIMIT 1;
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()
            if not row:
                return None
            return HiringSummary(
                id=row[0],
                total_jobs=row[1],
                total_companies=row[2],
                total_locations=row[3],
                remote_jobs=row[4],
                remote_percentage=row[5],
                average_salary=row[6],
                median_salary=row[7],
                highest_salary=row[8],
                highest_paying_company=row[9],
                top_company=row[10],
                top_skill=row[11],
                top_country=row[12],
                jobs_with_salary=row[13],
                jobs_without_salary=row[14],
                generation_timestamp=row[15],
                created_at=row[16],
                updated_at=row[17]
            )

    @staticmethod
    @track_db_time
    def get_freshness_metrics(conn) -> list[DatasetFreshness]:
        """
        Queries dataset status view to check refresh lag telemetry.
        """
        query = """
            SELECT dataset, last_refresh, current_age::TEXT, source_generation_timestamp, refresh_lag_minutes, status
            FROM serving.v_dataset_status
            ORDER BY dataset ASC;
        """
        with conn.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                DatasetFreshness(
                    dataset=row[0],
                    last_refresh=row[1],
                    current_age=row[2],
                    source_generation_timestamp=row[3],
                    refresh_lag_minutes=row[4],
                    status=row[5]
                )
                for row in rows
            ]
