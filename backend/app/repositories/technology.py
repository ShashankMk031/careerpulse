from backend.app.models.entities import TechnologyAnalytics
from backend.app.utils.context import track_db_time

class TechnologyRepository:
    ALLOWED_SORT_FIELDS = {
        "tech_tag", "job_demand_count", "avg_salary_min", "avg_salary_max", "top_company"
    }

    @classmethod
    @track_db_time
    def get_technology(
        cls, conn, limit: int, offset: int, sort_by: str, sort_order: str,
        search: str | None
    ) -> tuple[list[TechnologyAnalytics], int]:
        """
        Retrieves paginated, sorted, and filtered technology records, along with the total count.
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
            where_clauses.append("tech_tag ILIKE %s")
            params.append(f"%{search}%")
            
        where_str = ""
        if where_clauses:
            where_str = "WHERE " + " AND ".join(where_clauses)

        # Count total records matching criteria
        count_query = f"SELECT COUNT(*) FROM serving.technology_analytics {where_str};"
        
        # Query results
        query = f"""
            SELECT tech_tag, job_demand_count, avg_salary_min, avg_salary_max, top_company,
                   created_at, updated_at
            FROM serving.technology_analytics
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
            
            technology = [
                TechnologyAnalytics(
                    tech_tag=row[0],
                    job_demand_count=row[1],
                    avg_salary_min=row[2],
                    avg_salary_max=row[3],
                    top_company=row[4],
                    created_at=row[5],
                    updated_at=row[6]
                )
                for row in rows
            ]
            
            return technology, total_records
