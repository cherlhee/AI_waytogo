
main --> 

run --> 
get-sensor-data()
analyze()
	calculate-value()
	SCORE-FUNCTIONS()
	 
save-analysis()



rule.py
  │
  ├── get_sensor_data()
  │
  ├── get_standard()             ← 기존 함수 유지
  │
  ├── get_current_standard()     ← 새로 추가
  │
  ├── get_oiltemp_standard()     ← 새로 추가
  │
  ├── analyze()                  ← 기존 함수 수정
  │
  ├── save_analysis()
  │
  └── main()




ai_data
   │
   ├── io029 (주파수)
   ├── io001 (토출압력)
   ├── io045 (유량계 온도)
   │
   ▼
get_sensor_data()
   │
   ├── current
   │     ├── io029
   │     ├── io001
   │     └── io045
   │
   ▼
analyze()
   │
   ├── get_current_standard()
   │       │
   │       └── sp_get_current_std()
   │
   └── get_oiltemp_standard()
           │
           └── sp_get_oiltemp_std()