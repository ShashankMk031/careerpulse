from backend.app.models.entities import SkillAnalytics
from backend.app.utils.context import track_db_time

class SkillsRepository:
    ALLOWED_SORT_FIELDS = {
        "tag", "job_demand_count", "avg_salary_min", "avg_salary_max", 
        "salary_premium", "remote_jobs_count"
    }

    @classmethod
    @track_db_time
    def get_skills(
        cls, conn, limit: int, offset: int, sort_by: str, sort_order: str,
        search: str | None, min_demand: int | None
    ) -> tuple[list[SkillAnalytics], int]:
        """
        Retrieves paginated, sorted, and filtered skills, along with the total count.
        """
        # Validate sort parameters
        sort_col = sort_by.strip().lower()
        if sort_col not in cls.ALLOWED_SORT_FIELDS:
            sort_col = "job_demand_count"
            
        order = sort_order.strip().upper()
        if order not in ("ASC", "DESC"):
            order = "DESC"

        # Build SQL dynamic conditions
        where_clauses = []
        params = []
        
        if search:
            where_clauses.append("tag ILIKE %s")
            params.append(f"%{search}%")
            
        if min_demand is not None:
            where_clauses.append("job_demand_count >= %s")
            params.append(min_demand)
            
        where_str = ""
        if where_clauses:
            where_str = "WHERE " + " AND ".join(where_clauses)

        # Count total records matching criteria
        count_query = f"SELECT COUNT(*) FROM serving.skills_analytics {where_str};"
        
        # Query results
        query = f"""
            SELECT tag, job_demand_count, avg_salary_min, avg_salary_max, salary_premium,
                   remote_jobs_count, created_at, updated_at
            FROM serving.skills_analytics
            {where_str}
            ORDER BY {sort_col} {order}
            LIMIT %s OFFSET %s;
        """
        
        # Combine parameters
        query_params = list(params) + [limit, offset]
        
        with conn.cursor() as cursor:
            # 1. Get total records count
            cursor.execute(count_query, params)
            total_records = cursor.fetchone()[0]
            
            # 2. Get records
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            
            skills = [
                SkillAnalytics(
                    tag=row[0],
                    job_demand_count=row[1],
                    avg_salary_min=row[2],
                    avg_salary_max=row[3],
                    salary_premium=row[4],
                    remote_jobs_count=row[5],
                    created_at=row[6],
                    updated_at=row[7]
                )
                for row in rows
            ]
            
            return skills, total_records
