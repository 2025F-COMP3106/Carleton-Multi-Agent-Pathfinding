import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt


def statistical_analysis(csv_path="results/comparison_results.csv"):
    # load data
    df = pd.read_csv(csv_path)
    print(f"\nLoaded {len(df)} simulations\n")

    # calculate improvement
    df["improvement"] = df["intelligent_time"] - df["naive_time"]

    # calculate efficiency (social time gained per minute of deviation)
    df["efficiency"] = df["improvement"] / df["deviation_cost"]
    df["efficiency"] = df["efficiency"].replace([float('inf'), -float('inf')], 0)  # handle division by zero

    # descriptive stats
    print("=" * 50)
    print("DESCRIPTIVE STATISTICS")
    print("=" * 50)
    print(
        f"Intelligent Agent: mean = {df['intelligent_time'].mean():.2f} min, "
        f"median = {df['intelligent_time'].median():.2f} min, "
        f"std = {df['intelligent_time'].std():.2f} min"
    )
    print(
        f"Naive Agent:       mean = {df['naive_time'].mean():.2f} min, "
        f"median = {df['naive_time'].median():.2f} min, "
        f"std = {df['naive_time'].std():.2f} min"
    )
    print(f"Mean Improvement:  {df['improvement'].mean():.2f} min")
    print()
    print(
        f"Path Deviation:    mean = {df['deviation_cost'].mean():.2f} min, "
        f"median = {df['deviation_cost'].median():.2f} min, "
        f"std = {df['deviation_cost'].std():.2f} min"
    )
    print(
        f"Efficiency:        {df['efficiency'].mean():.2f} social min per deviation min "
        f"(higher is better)"
    )
    print()

    # paired t-test
    print("=" * 50)
    print("PAIRED T-TEST")
    print("=" * 50)
    t_stat, p_value = stats.ttest_rel(df["intelligent_time"], df["naive_time"])
    print(f"t-statistic: {t_stat:.4f}")
    print(f"p-value:     {p_value:.6f}")

    if p_value < 0.05:
        print(f"\nResult: SIGNIFICANT (p < 0.05)")
        print(
            "The intelligent agent performs significantly better than the naive agent."
        )
    else:
        print(f"\nResult: NOT SIGNIFICANT (p >= 0.05)")
        print("No significant difference between intelligent and naive agents.")
    print()

    # box plot
    print("=" * 50)
    print("GENERATING PLOTS")
    print("=" * 50)

    # plot 1: social time comparison
    _, ax = plt.subplots(figsize=(8, 6))
    data_to_plot = [df["intelligent_time"], df["naive_time"]]

    # show mean as red dashed line, median as solid line in box
    ax.boxplot(data_to_plot, tick_labels=["Intelligent Agent", "Naive Agent"],
               showmeans=True, meanline=True,
               meanprops=dict(linestyle='--', linewidth=2, color='red'))

    ax.set_ylabel("Social Score (minutes)")
    ax.set_title("Intelligent vs Naive Agent Comparison\n(Red dashed line = mean, orange line in box = median)")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("results/comparison_boxplot.png", dpi=150)
    plt.close()
    print("Saved: results/comparison_boxplot.png")

    # plot 2: deviation vs social time gained (only non-zero social time)
    _, ax = plt.subplots(figsize=(8, 6))
    df_nonzero = df[df["improvement"] > 0]
    ax.scatter(df_nonzero["deviation_cost"], df_nonzero["improvement"], alpha=0.6, s=100)
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='No improvement')
    ax.axvline(x=0, color='r', linestyle='--', alpha=0.5)
    ax.set_xlabel("Path Deviation (minutes)")
    ax.set_ylabel("Social Time Improvement (minutes)")
    ax.set_title(f"Trade-off: Deviation Cost vs Social Time Gained\n(showing {len(df_nonzero)} of {len(df)} simulations with social time > 0)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("results/deviation_vs_improvement.png", dpi=150)
    plt.close()
    print("Saved: results/deviation_vs_improvement.png\n")


if __name__ == "__main__":
    statistical_analysis()
