from backend.app.models.entities import GeographyAnalytics
from backend.app.utils.context import track_db_time

class GeographyRepository:
    ALLOWED_SORT_FIELDS = {
        "country", "region", "jobs_count", "avg_salary_min", "avg_salary_max",
        "company_count", "remote_count", "onsite_count", "hybrid_count"
    }

    @classmethod
    @track_db_time
    def get_geography(
        cls, conn, country: str | None, remote: bool | None, sort_by: str, sort_order: str
    ) -> list[GeographyAnalytics]:
        """
        Retrieves geography analytics with optional country and remote filters.
        """
        # Validate sort parameters
        sort_col = sort_by.strip().lower()
        if sort_col not in cls.ALLOWED_SORT_FIELDS:
            sort_col = "jobs_count"
            
        order = sort_order.strip().upper()
        if order not in ("ASC", "DESC"):
            order = "DESC"

        # Build SQL dynamic conditions
        where_clauses = []
        params = []
        
        if country:
            where_clauses.append("country ILIKE %s")
            params.append(f"%{country}%")
            
        if remote is not None:
            if remote:
                where_clauses.append("(country = 'Remote' OR region = 'Remote' OR remote_count > 0)")
            else:
                where_clauses.append("(country != 'Remote' AND region != 'Remote')")
                
        where_str = ""
        if where_clauses:
            where_str = "WHERE " + " AND ".join(where_clauses)

        query = f"""
            SELECT country, region, jobs_count, avg_salary_min, avg_salary_max, company_count,
                   remote_count, onsite_count, hybrid_count, created_at, updated_at
            FROM serving.geography_analytics
            {where_str}
            ORDER BY {sort_col} {order};
        """
        
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                GeographyAnalytics(
                    country=row[0],
                    region=row[1],
                    jobs_count=row[2],
                    avg_salary_min=row[3],
                    avg_salary_max=row[4],
                    company_count=row[5],
                    remote_count=row[6],
                    onsite_count=row[7],
                    hybrid_count=row[8],
                    created_at=row[9],
                    updated_at=row[10]
                )
                for row in rows
            ]
