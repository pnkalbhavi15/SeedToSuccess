# Load the required packages
library(dplyr)
library(lubridate)
library(ggplot2)
library(tidyr)

library(tidyverse)

list.files(path = "../input")

# Load the dataset from a CSV file
data <- read.csv("prices.csv", stringsAsFactors = FALSE)

# Check for missing values
missing_values <- sum(is.na(data))
cat("Number of missing values:", missing_values, "\n")

# Handle missing values (remove or impute)
# To remove rows with missing values:
data <- data[complete.cases(data), ]

# To impute missing values with the mean:
data$modal_price <- ifelse(is.na(data$modal_price), mean(data$modal_price, na.rm = TRUE), data$modal_price)

# Convert "arrival_date" column to a suitable date format
data$arrival_date <- as.Date(data$arrival_date, format = "%m/%d/%Y")

# Get unique values of commodities
commodity_list <- unique(data$commodity)

# Print the lists
# print("List of Commodities:")
# print(commodity_list)

# Get unique values of varieties
variety_list <- unique(data$variety)

# Print the lists
# print("List of Varieties:")
# print(variety_list)

# Get unique values of districts
district_list <- unique(data$district)

# Print the lists
# print("List of Districts:")
# print(district_list)

# Get unique values of markets
market_list <- unique(data$market)

# Print the lists
# print("List of Markets:")
# print(market_list)

# Explore and clean the data
# Check for data integrity and consistency
summary(data)
str(data)

# Perform additional data cleaning steps if necessary
# For example, removing duplicate rows:
data <- distinct(data)

# Print the cleaned dataset
# print(data)

# Calculate basic statistics for numerical columns
num_stats <- data %>%
  summarise(
    min_price_mean = mean(min_price),
    min_price_median = median(min_price),
    min_price_mode = names(which.max(table(min_price))),
    min_price_range = max(min_price) - min(min_price),
    min_price_sd = sd(min_price),
    max_price_mean = mean(max_price),
    max_price_median = median(max_price),
    max_price_mode = names(which.max(table(max_price))),
    max_price_range = max(max_price) - min(max_price),
    max_price_sd = sd(max_price),
    modal_price_mean = mean(modal_price),
    modal_price_median = median(modal_price),
    modal_price_mode = names(which.max(table(modal_price))),
    modal_price_range = max(modal_price) - min(modal_price),
    modal_price_sd = sd(modal_price)
  )

print(num_stats)

# Identify unique values and their frequencies for categorical columns
cat_stats <- data %>%
  summarise(
    state_unique = n_distinct(state),
    state_freq = n(),
    district_unique = n_distinct(district),
    district_freq = n(),
    market_unique = n_distinct(market),
    market_freq = n(),
    commodity_unique = n_distinct(commodity),
    commodity_freq = n(),
    variety_unique = n_distinct(variety),
    variety_freq = n()
  )

print(cat_stats)

# Histogram for min_price
hist_min_price <- ggplot(data, aes(x = min_price)) +
  geom_histogram(fill = "lightblue", color = "black") +
  labs(title = "Histogram of Minimum Price", x = "Minimum Price", y = "Frequency")

# Box plot for max_price
boxplot_max_price <- ggplot(data, aes(x = "", y = max_price)) +
  geom_boxplot(fill = "lightgreen", color = "black") +
  labs(title = "Box Plot of Maximum Price", x = "", y = "Maximum Price")

# Bar chart for state frequencies
barplot_state_freq <- ggplot(data, aes(x = state)) +
  geom_bar(fill = "lightpink", color = "black") +
  labs(title = "State Frequencies", x = "State", y = "Frequency") +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  geom_text(stat = "count", aes(label = after_stat(count)), vjust = -0.5)

# Bar chart for commodity frequencies
barchart_for_commodity_freq <- ggplot(data, aes(x = commodity)) +
  geom_bar(fill = "lightyellow", color = "black") +
  labs(title = "Commodity Frequencies", x = "Commodity", y = "Frequency") +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  geom_text(stat = "count", aes(label = after_stat(count)), vjust = -0.5)

# Histogram for modal_price
histogram_for_modal_price <- ggplot(data, aes(x = modal_price)) +
  geom_histogram(fill = "lightcyan", color = "black") +
  labs(title = "Histogram of Modal Price", x = "Modal Price", y = "Frequency")

# Box plot for min_price
boxplot_for_min_price <- ggplot(data, aes(x = "", y = min_price)) +
  geom_boxplot(fill = "lightpink", color = "black") +
  labs(title = "Box Plot of Minimum Price", x = "", y = "Minimum Price")


# Bar chart for district frequencies
barchart_for_distinct_freq <- ggplot(data, aes(x = district)) +
  geom_bar(fill = "lightgreen", color = "black") +
  labs(title = "District Frequencies", x = "District", y = "Frequency") +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  geom_text(stat = "count", aes(label = after_stat(count)), vjust = -0.5)

# Bar chart for market frequencies
barchart_for_market_freq <- ggplot(data, aes(x = market)) +
  geom_bar(fill = "lightblue", color = "black") +
  labs(title = "Market Frequencies", x = "Market", y = "Frequency") +
  theme(axis.text.x = element_text(angle = 90, hjust = 1)) +
  geom_text(stat = "count", aes(label = after_stat(count)), vjust = -0.5)

# Scatter plot for min_price vs. max_price
scatterplot_for_min_vs_max_price <- ggplot(data, aes(x = min_price, y = max_price)) +
geom_point(color = "darkorange") +
labs(title = "Scatter Plot of Minimum Price vs. Maximum Price", x = "Minimum Price", y = "Maximum Price")
  
library(GGally)
# Install corrplot package if not already installed
if (!require(corrplot)) {
  install.packages("corrplot")
}

# Load the corrplot package
library(corrplot)

options(repr.plot.width = 3, repr.plot.height = 2.5)

# Visualize the distributions of average prices
avg_price <- ggplot(data, aes(x = modal_price)) +
  geom_histogram(fill = "steelblue", color = "white", bins = 30) +
  labs(x = "Modal Price", y = "Count", title = "Distribution of Modal Prices") +
  theme_minimal()

# Select the columns for correlation
cor_columns <- c("min_price", "max_price", "modal_price")

# Calculate correlations
correlation_matrix <- cor(data[, cor_columns])

# Visualize the correlation matrix
corrplot(correlation_matrix, method = "color", type = "upper", tl.cex = 0.8, tl.col = "black")

# Save the plots as images
ggsave("static/plots/hist_min_price.png", hist_min_price, width = 800, height = 600)
ggsave("static/plots/boxplot_max_price.png", boxplot_max_price, width = 800, height = 600)
ggsave("static/plots/barplot_state_freq.png", barplot_state_freq, width = 800, height = 600)
ggsave("static/plots/barchart_for_commodity_freq.png", barchart_for_commodity_freq, width = 800, height = 600)
ggsave("static/plots/histogram_for_modal_price.png", histogram_for_modal_price, width = 800, height = 600)
ggsave("static/plots/boxplot_for_min_price.png", boxplot_for_min_price, width = 800, height = 600)
ggsave("static/plots/barchart_for_distinct_freq.png", barchart_for_distinct_freq, width = 800, height = 600)
ggsave("static/plots/barchart_for_market_freq.png", barchart_for_market_freq, width = 800, height = 600)
ggsave("static/plots/scatterplot_for_min_vs_max_price.png", scatterplot_for_min_vs_max_price, width = 800, height = 600)
ggsave("static/plots/avg_price.png", avg_price, width = 800, height = 600)
# Add similar lines for other plots