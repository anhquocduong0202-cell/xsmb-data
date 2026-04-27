import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Load dữ liệu
df = pd.read_csv('xsmb.csv')

# Hàm để lấy 2 số cuối từ một số
def get_last_two_digits(num):
    return str(int(num))[-2:] if pd.notna(num) else None

# Hàm để tạo tín hiệu dự đoán (pattern đơn giản)
def generate_signal(df, lookback=3):
    """
    Tạo tín hiệu dự đoán dựa trên các mẫu quá khứ
    Sử dụng chiến lược: nếu 2 số cuối của 3 ngày liên tiếp là giống nhau, 
    dự đoán nó sẽ xuất hiện tiếp theo
    """
    signals = []
    
    for i in range(len(df)):
        if i < lookback:
            signals.append(None)
        else:
            # Lấy 2 số cuối từ cột special của 3 ngày trước
            past_values = []
            for j in range(1, lookback + 1):
                val = get_last_two_digits(df.iloc[i-j]['special'])
                if val:
                    past_values.append(val)
            
            # Nếu có pattern, dự đoán lặp lại
            if len(past_values) >= 2 and past_values[0] == past_values[1]:
                signals.append(past_values[0])
            else:
                signals.append(None)
    
    return signals

# Hàm để lấy tất cả 2 số cuối từ các cột prize
def get_all_prize_last_two_digits(row):
    """
    Trích xuất 2 số cuối từ tất cả các cột prize trong một hàng
    """
    prize_cols = [col for col in row.index if col.startswith('prize')]
    last_two_digits = set()
    
    for col in prize_cols:
        last_two = get_last_two_digits(row[col])
        if last_two:
            last_two_digits.add(last_two)
    
    return last_two_digits

# Tạo tín hiệu
df['signal'] = generate_signal(df, lookback=3)

# Tạo tập hợp các 2 số cuối từ prizes cho mỗi hàng
df['actual_last_two'] = df.apply(get_all_prize_last_two_digits, axis=1)

# Hàm để kiểm tra nếu tín hiệu khớp với actual
def check_hit(signal, actual_set):
    if signal is None or len(actual_set) == 0:
        return False
    return signal in actual_set

# Kiểm tra hit
df['hit'] = df.apply(lambda row: check_hit(row['signal'], row['actual_last_two']), axis=1)

# Bắt đầu backtest từ ngày có tín hiệu (lookback + 1)
backtest_df = df[df['signal'].notna()].copy()

print("=" * 80)
print("BACKTEST XSMB - Pattern Matching Strategy")
print("=" * 80)
print(f"\nThời kỳ: {df['date'].iloc[0]} đến {df['date'].iloc[-1]}")
print(f"Tổng số ngày: {len(df)}")
print(f"Số ngày có tín hiệu: {len(backtest_df)}")

# Thống kê cơ bản
hits = backtest_df['hit'].sum()
total_signals = len(backtest_df)
win_rate = (hits / total_signals * 100) if total_signals > 0 else 0

print(f"\n{'KẾT QUẢ BACKTEST:':^80}")
print("-" * 80)
print(f"Tổng tín hiệu: {total_signals}")
print(f"Tín hiệu trúng: {hits}")
print(f"Tín hiệu miss: {total_signals - hits}")
print(f"Win Rate: {win_rate:.2f}%")

# Backtest với giả định đặt cược
print(f"\n{'BET ANALYSIS (Assuming 1 unit per bet):':^80}")
print("-" * 80)

initial_capital = 1000  # Vốn ban đầu
bet_amount = 10  # Số tiền cược mỗi lần
odds = 99  # Tỷ lệ trả thưởng nếu trúng (99:1 là điển hình cho xổ số)

balance = initial_capital
total_bets = 0
total_winnings = 0
daily_records = []

for idx, row in backtest_df.iterrows():
    signal = row['signal']
    is_hit = row['hit']
    
    balance -= bet_amount  # Trừ tiền cược
    total_bets += bet_amount
    
    if is_hit:
        winnings = bet_amount * odds
        balance += winnings
        total_winnings += winnings
        result = "HIT"
        profit = winnings - bet_amount
    else:
        result = "MISS"
        profit = -bet_amount
    
    daily_records.append({
        'date': row['date'],
        'signal': signal,
        'actual': ', '.join(sorted(row['actual_last_two'])),
        'result': result,
        'balance': balance,
        'profit': profit
    })

# Tổng hợp kết quả
total_profit = balance - initial_capital
roi = (total_profit / initial_capital) * 100

print(f"Vốn ban đầu: {initial_capital:,.0f} đơn vị")
print(f"Tổng tiền cược: {total_bets:,.0f} đơn vị")
print(f"Tổng tiền thắng: {total_winnings:,.0f} đơn vị")
print(f"Vốn cuối cùng: {balance:,.0f} đơn vị")
print(f"Lợi nhuận: {total_profit:,.0f} đơn vị")
print(f"ROI: {roi:.2f}%")

# Chi tiết từng ngày (hiển thị 20 hàng đầu)
print(f"\n{'CHI TIẾT CÁC NGÀY (20 hàng đầu):':^80}")
print("-" * 80)
print(f"{'Date':<12} {'Signal':<8} {'Actual':<30} {'Result':<8} {'Balance':<12} {'Profit':<8}")
print("-" * 80)

for i, record in enumerate(daily_records[:20]):
    print(f"{record['date']:<12} {record['signal']:<8} {record['actual']:<30} {record['result']:<8} {record['balance']:<12.0f} {record['profit']:<8}")

if len(daily_records) > 20:
    print(f"\n... ({len(daily_records) - 20} hàng khác)")

# Phân tích thêm
print(f"\n{'PHÂN TÍCH CHI TIẾT:':^80}")
print("-" * 80)

hit_records = [r for r in daily_records if r['result'] == 'HIT']
miss_records = [r for r in daily_records if r['result'] == 'MISS']

if hit_records:
    avg_profit_per_hit = sum(r['profit'] for r in hit_records) / len(hit_records)
    print(f"Trung bình lợi nhuận mỗi lần trúng: {avg_profit_per_hit:.2f} đơn vị")
else:
    print(f"Trung bình lợi nhuận mỗi lần trúng: 0.00 đơn vị (không có trúng)")

avg_loss_per_miss = -bet_amount if miss_records else 0
print(f"Trung bình thua lỗ mỗi lần miss: {avg_loss_per_miss:.2f} đơn vị")

# Tìm streak tốt nhất và xấu nhất
best_streak = 0
worst_streak = 0
current_streak = 0

for record in daily_records:
    if record['result'] == 'HIT':
        current_streak += 1
        best_streak = max(best_streak, current_streak)
    else:
        worst_streak = max(worst_streak, abs(current_streak))
        current_streak = -1

worst_streak = max(worst_streak, abs(current_streak))

print(f"Best streak (liên tiếp trúng): {best_streak} ngày")
print(f"Worst streak (liên tiếp miss): {worst_streak} ngày")

print("\n" + "=" * 80)

# Lưu kết quả chi tiết ra file CSV
results_df = pd.DataFrame(daily_records)
results_df.to_csv('backtest_results.csv', index=False)
print(f"\n✓ Chi tiết backtest đã lưu vào 'backtest_results.csv'")

# Tạo summary stats
summary = {
    'Total Days': len(df),
    'Signal Days': total_signals,
    'Hits': hits,
    'Misses': total_signals - hits,
    'Win Rate (%)': f"{win_rate:.2f}",
    'Initial Capital': initial_capital,
    'Final Capital': balance,
    'Total Profit': total_profit,
    'ROI (%)': f"{roi:.2f}",
    'Best Streak': best_streak,
    'Worst Streak': worst_streak
}

summary_df = pd.DataFrame([summary])
summary_df.to_csv('backtest_summary.csv', index=False)
print(f"✓ Tóm tắt kết quả đã lưu vào 'backtest_summary.csv'")
