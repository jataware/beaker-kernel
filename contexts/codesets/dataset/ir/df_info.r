library(jsonlite)
.result = list()

for (.var_name in ls()) {
    .df <- get(.var_name)
    if (is.data.frame(.df)) {
        .col_names <- names(.df)
        .head <- list(as.list(.col_names))
        for (.i in 1:30) {
            .row <- list()
            for (.col_name in .col_names) {
                .row<-append(.row, .df[[.col_name]][.i])
            }
            .head<-append(.head, list(.row))
        }
        .col_types <- as.list(sapply(.df, class))
        .col_stats <- toString(as.list(lapply(.df, summary)))
        .row_info <- list( columns = .col_names, datatypes = .col_types, head = .head, statistics = .col_stats)
        .result[[.var_name]] <- .row_info
    }
}

.p <- toJSON(.result, auto_unbox = TRUE)
.f <- toString(.p)
print(.f)