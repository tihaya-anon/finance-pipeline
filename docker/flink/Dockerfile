FROM apache/flink:1.19.2-scala_2.12-java11

ARG FLINK_VERSION=1.19.2
ARG KAFKA_CONNECTOR_VERSION=3.2.0-1.19

RUN curl -fsSL "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/${KAFKA_CONNECTOR_VERSION}/flink-sql-connector-kafka-${KAFKA_CONNECTOR_VERSION}.jar" \
    -o "/opt/flink/lib/flink-sql-connector-kafka-${KAFKA_CONNECTOR_VERSION}.jar" \
    && curl -fsSL "https://repo1.maven.org/maven2/org/apache/flink/flink-json/${FLINK_VERSION}/flink-json-${FLINK_VERSION}.jar" \
    -o "/opt/flink/lib/flink-json-${FLINK_VERSION}.jar"

COPY sql /opt/flink/sql
