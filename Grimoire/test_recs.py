from grimoire.models import SessionLocal
from grimoire import jobs

db = SessionLocal()

print("Calculating matrix...")
matrix = jobs.get_normalized_matrix(db)
print("Matrix shape:", matrix.shape)

users = matrix["username"].to_list()
if users:
    target = users[0]
    print(f"Testing recommendations for {target}...")
    top_books, top_users = jobs.calculate_recommendations(db, target, matrix_df=matrix)
    print("Top Books:", top_books)
    print("Top Users:", top_users)
else:
    print("No users in matrix!")
