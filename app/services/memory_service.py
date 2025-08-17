from app.services.vector_db_service import VectorDBService

class MemoryService:
    def __init__(self):
        self.vector_db = VectorDBService()

    def get_today_summaries(self, user_query, user_id, yymmdd, top_k=2, threshold=0.4):
        # 오늘 날짜(yymmdd) + user_id로 필터, 유사도 0.6 이상, 최대 2개
        results = self.vector_db.search_similar(
            user_query,
            top_k=top_k,
            filter={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"date": {"$eq": yymmdd}}
                ]
            },
            threshold=threshold
        )
        
        # 결과가 없으면 임계값 없이 재검색
        # if len(results) == 0:
        #     results = self.vector_db.search_similar(
        #         user_query,
        #         top_k=top_k,
        #         filter={
        #             "$and": [
        #                 {"user_id": {"$eq": user_id}},
        #                 {"date": {"$eq": yymmdd}}
        #             ]
        #         },
        #         threshold=None
        #     )
        
        return results

    def get_past_summaries(self, user_query, user_id, yymmdd, top_k=2, threshold=0.45):
        # 오늘 날짜(yymmdd)가 아닌 것 + user_id로 필터, 유사도 0.65 이상, 최대 2개
        results = self.vector_db.search_similar(
            user_query,
            top_k=top_k,
            filter={
                "$and": [
                    {"user_id": {"$eq": user_id}},
                    {"date": {"$ne": yymmdd}}
                ]
            },
            threshold=threshold
        )
        
        # # 결과가 없으면 임계값 없이 재검색
        # if len(results) == 0:
        #     results = self.vector_db.search_similar(
        #         user_query,
        #         top_k=top_k,
        #         filter={
        #             "$and": [
        #                 {"user_id": {"$eq": user_id}},
        #                 {"date": {"$ne": yymmdd}}
        #             ]
        #         },
        #         threshold=None
        #     )
        
        return results 