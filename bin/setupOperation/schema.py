# coding: utf-8
# from sqlalchemy import CHAR, Column, DateTime, Enum, ForeignKey, ForeignKeyConstraint, Index, String, Table, Text, Time, text
from sqlalchemy import *
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TINYINT
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.sql import select, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import create_view

Base = declarative_base()
metadata = Base.metadata


class dbVersion(Base):
    __tablename__ = 'db_version'

    version = Column(Integer, nullable=False, primary_key=True, comment='Version of deployed DBImport schema')
    install_date = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class airflowCustomDag(Base):
    __tablename__ = 'airflow_custom_dags'

    dag_name = Column(String(64), primary_key=True, comment='Name of Airflow DAG.')
    schedule_interval = Column(String(20), nullable=False, comment='Time to execute dag', server_default=text("'None'"))
    retries = Column(INTEGER(11), nullable=False, server_default=text("'0'"))
    operator_notes = Column(Text, comment='Free text field to write a note about the import. ')
    application_notes = Column(Text, comment='Free text field that can be used for application documentaton, notes or links. ')


class airflowDagSensor(Base):
    __tablename__ = 'airflow_dag_sensors'

    dag_name = Column(String(64), primary_key=True, nullable=False, comment='Name of DAG to add sensor to')
    sensor_name = Column(String(64), primary_key=True, nullable=False, comment='name of the sensor Task')
    wait_for_dag = Column(String(64), nullable=False, comment='Name of DAG to wait for. Must be defined in DBImport')
    wait_for_task = Column(String(64), comment="Name of task to wait for.Default is 'stop'")
    timeout_minutes = Column(INTEGER(11), comment='Number of minutes to wait for DAG.')


# class AirflowDagTriggers(Base):
#     __tablename__ = 'airflow_dag_triggers'
# 
#     dag_name = Column(String(64))
#     trigger_name = Column(Text)
#     dag_to_trigger = Column(Text)
# 

class airflowEtlDag(Base):
    __tablename__ = 'airflow_etl_dags'

    dag_name = Column(String(64), primary_key=True, comment='Name of Airflow DAG.')
    schedule_interval = Column(String(20), nullable=False, comment='Time to execute dag', server_default=text("'None'"))
    filter_job = Column(String(64), nullable=False)
    filter_task = Column(String(64))
    filter_source_db = Column(String(256))
    filter_target_db = Column(String(256))
    retries = Column(TINYINT(4))
    trigger_dag_on_success = Column(String(64))
    operator_notes = Column(Text, comment='Free text field to write a note about the import. ')
    application_notes = Column(Text, comment='Free text field that can be used for application documentaton, notes or links. ')


class airflowExecutionType(Base):
    __tablename__ = 'airflow_execution_type'

    executionid = Column(INTEGER(11), primary_key=True)
    execution_type = Column(Text, nullable=False)


class airflowExportDag(Base):
    __tablename__ = 'airflow_export_dags'

    dag_name = Column(String(64), primary_key=True, comment='Name of Airflow DAG.')
    schedule_interval = Column(String(20), nullable=False, comment='Time to execute dag', server_default=text("'None'"))
    filter_dbalias = Column(String(256), nullable=False, comment='Filter string for DBALIAS in export_tables')
    filter_target_schema = Column(String(256), comment='Filter string for TARGET_SCHEMA  in export_tables')
    filter_target_table = Column(String(256), comment='Filter string for TARGET_TABLE  in export_tables')
    use_python_dbimport = Column(TINYINT(4), nullable=False, server_default=text("'1'"))
    retries = Column(TINYINT(4))
    trigger_dag_on_success = Column(String(64), comment='Name of DAG to trigger if export is successfull. Comma seperated list of DAGs (optional)')
    operator_notes = Column(Text, comment='Free text field to write a note about the import. ')
    application_notes = Column(Text, comment='Free text field that can be used for application documentaton, notes or links. ')


class airflowImportDag(Base):
    __tablename__ = 'airflow_import_dags'

    dag_name = Column(String(64), primary_key=True, comment='Name of Airflow DAG.')
    schedule_interval = Column(String(32), nullable=False, comment='Time to execute dag', server_default=text("'None'"))
    filter_hive = Column(String(256), nullable=False, comment='Filter string for database and table. ; separated. Wildcards (*) allowed. Example HIVE_DB.HIVE_TABLE; HIVE_DB.HIVE_TABLE')
    filter_hive_db_OLD = Column(String(256), comment='NOT USED: Filter string for HIVE_DB in import_tables')
    filter_hive_table_OLD = Column(String(256), comment='NOT USED: Filter string for HIVE_TABLE in import_tables')
    use_python_dbimport = Column(TINYINT(4), nullable=False, server_default=text("'1'"))
    finish_all_stage1_first = Column(TINYINT(4), nullable=False, server_default=text("'0'"))
    retries = Column(TINYINT(4), nullable=False, server_default=text("'5'"))
    retries_stage1 = Column(TINYINT(4))
    retries_stage2 = Column(TINYINT(4))
    pool_stage1 = Column(String(256), comment='Airflow pool used for stage1 tasks. NULL for default pool')
    pool_stage2 = Column(String(256), comment='Airflow pool used for stage2 tasks. NULL for default pool')
    operator_notes = Column(Text, comment='Free text field to write a note about the import. ')
    application_notes = Column(Text, comment='Free text field that can be used for application documentaton, notes or links. ')
    auto_table_discovery = Column(TINYINT(4), nullable=False, server_default=text("'1'"))


class autoDiscoveredTable(Base):
    __tablename__ = 'auto_discovered_tables'

    hive_db = Column(String(256), primary_key=True, nullable=False)
    dbalias = Column(String(256), primary_key=True, nullable=False)
    source_schema = Column(String(256), primary_key=True, nullable=False)
    source_table = Column(String(256), primary_key=True, nullable=False)
    discovery_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    migrate_to_import_tables = Column(TINYINT(4), nullable=False, server_default=text("'0'"))


class configuration(Base):
    __tablename__ = 'configuration'
    __table_args__ = {'comment': 'This is the DBImport global configuration table. In here you can configure items such as the name of the staging database, disable global executions, max number of mappers and much more. '}

    configKey = Column(String(32), primary_key=True, comment='Name of the configuration item. These are controlled and maintained by thee setup tool. Dont change these manually')
    valueInt = Column(INTEGER(11), comment='Integer based Value')
    valueStr = Column(String(256), comment='String based Value')
    valueDate = Column(DateTime, comment='Date based Value')
    description = Column(Text, comment='Description on the setting')


class etlJobs(Base):
    __tablename__ = 'etl_jobs'

    job = Column(String(64), primary_key=True, nullable=False)
    task = Column(String(64), primary_key=True, nullable=False)
    job_id = Column(INTEGER(11), nullable=False, unique=True, autoincrement=True)
    etl_type = Column(String(32), nullable=False, server_default=text("'0'"))
    include_in_airflow = Column(TINYINT(4), nullable=False, server_default=text("'1'"))
    source_db = Column(String(256))
    source_table = Column(String(256))
    target_db = Column(String(256))
    target_table = Column(String(256))
    operator_notes = Column(String(256), comment='Free text field to write a note about the import. ')


class exportRetriesLog(Base):
    __tablename__ = 'export_retries_log'
    __table_args__ = {'comment': 'Log of all retries that have happened. '}

    dbalias = Column(String(256), primary_key=True, nullable=False, comment='Database connection name that we export to')
    target_schema = Column(String(256), primary_key=True, nullable=False, comment='Schema on the target system')
    target_table = Column(String(256), primary_key=True, nullable=False, comment='Table on the target system')
    retry_time = Column(DateTime, primary_key=True, nullable=False, comment='Time when the retry was started')
    stage = Column(INTEGER(11), nullable=False, comment="The stage of the import that the retry started from. This is an internal stage and has nothing to do with stage1 and stage2 in Airflow DAG's")
    stage_description = Column(Text, nullable=False, comment='Description of the stage')


class exportStage(Base):
    __tablename__ = 'export_stage'
    __table_args__ = {'comment': 'The export tool keeps track of how far in the export the tool have succeeded. So in case of an error, lets say that Hive is not responding, the next time an export is executed it will skip the first part and continue from where it ended in error on the previous run. If you want to rerun from the begining, the information in this table needs to be cleared. This is done with the "manage --clearExportStage" tool. Keep in mind that clearing the stage of an incremental export might result in the loss of the data.'}

    dbalias = Column(String(256), primary_key=True, nullable=False, comment='Database connection name that we export to')
    target_schema = Column(String(256), primary_key=True, nullable=False, comment='Schema on the target system')
    target_table = Column(String(256), primary_key=True, nullable=False, comment='Table on the target system')
    stage = Column(INTEGER(11), nullable=False, comment='Current stage of the export. This is the internal stage number')
    stage_description = Column(Text, nullable=False, comment='Description of the stage')
    stage_time = Column(DateTime, comment='The date and time when the import entered the stage')


class exportStageStatistic(Base):
    __tablename__ = 'export_stage_statistics'
    __table_args__ = {'comment': 'As DBImport progress through the different stages of the export, it also keeps track of start and stop time for each stage together with the duration. That information is kept in this table'}

    dbalias = Column(String(256), primary_key=True, nullable=False, comment='Database connection name that we export to')
    target_schema = Column(String(256), primary_key=True, nullable=False, comment='Schema on the target system')
    target_table = Column(String(256), primary_key=True, nullable=False, comment='Table on the target system')
    stage = Column(INTEGER(11), primary_key=True, nullable=False, comment='Current stage of the export. This is the internal stage number')
    start = Column(DateTime, nullable=False, comment='Time when stage started')
    stop = Column(DateTime, nullable=False, comment='Time when stage was completed')
    duration = Column(INTEGER(11), nullable=False, comment='Duration of stage')


class exportStatistic(Base):
    __tablename__ = 'export_statistics'
    __table_args__ = (
        Index('dbalias_target_schema_target_table', 'dbalias', 'target_schema', 'target_table'),
        {'comment': "At the end of each export, all statistics about how long each part took aswell as general information about Hive database and table, number of rows imported, size of the export and much more are logged in this table. This table grows and will never be truncated by DBImport itself. If it becomes to large for you, it's up to each user to delete or truncate this table as you see fit."}
    )

    id = Column(BIGINT(20), primary_key=True, autoincrement=True, comment='Auto incremented PrimaryKey of the table')
    dbalias = Column(String(256), comment='ID of the Database Connection')
    target_database = Column(String(256), comment='Name of the source database')
    target_schema = Column(String(256), comment='Name of the source schema')
    target_table = Column(String(256), comment='Name of the source table')
    hive_db = Column(String(256), comment='Hive Database')
    hive_table = Column(String(256), comment='Hive Table')
    export_phase = Column(String(32), comment='Import Phase method')
    incremental = Column(TINYINT(4), comment='0 = Full import, 1 = Incremental import')
    rows = Column(BIGINT(20), comment='How many rows that was imported')
    size = Column(BIGINT(20), comment='The total size in bytes that was imported')
    sessions = Column(TINYINT(4), comment='How many parallell sessions was used against the source (sqoop mappers)')
    duration = Column(INTEGER(11), comment='Tota duration in seconds')
    start = Column(DateTime, comment='Timestamp of start')
    stop = Column(DateTime, comment='Timestamp of stop')
    get_hive_tableschema_duration = Column(INTEGER(11))
    get_hive_tableschema_start = Column(DateTime)
    get_hive_tableschema_stop = Column(DateTime)
    clear_table_rowcount_duration = Column(INTEGER(11))
    clear_table_rowcount_start = Column(DateTime)
    clear_table_rowcount_stop = Column(DateTime)
    create_temp_table_duration = Column(INTEGER(11))
    create_temp_table_start = Column(DateTime)
    create_temp_table_stop = Column(DateTime)
    truncate_temp_table_duration = Column(INTEGER(11))
    truncate_temp_table_start = Column(DateTime)
    truncate_temp_table_stop = Column(DateTime)
    fetch_maxvalue_start = Column(DateTime)
    fetch_maxvalue_stop = Column(DateTime)
    fetch_maxvalue_duration = Column(INTEGER(11))
    insert_into_temp_table_duration = Column(INTEGER(11))
    insert_into_temp_table_start = Column(DateTime)
    insert_into_temp_table_stop = Column(DateTime)
    create_target_table_duration = Column(INTEGER(11))
    create_target_table_start = Column(DateTime)
    create_target_table_stop = Column(DateTime)
    truncate_target_table_duration = Column(INTEGER(11))
    truncate_target_table_start = Column(DateTime)
    truncate_target_table_stop = Column(DateTime)
    sqoop_duration = Column(INTEGER(11))
    sqoop_start = Column(DateTime)
    sqoop_stop = Column(DateTime)
    validate_duration = Column(INTEGER(11))
    validate_start = Column(DateTime)
    validate_stop = Column(DateTime)


class exportStatisticsLast(Base):
    __tablename__ = 'export_statistics_last'
    __table_args__ = {'comment': 'The last entry in table export_statistics is also stored in this table. This makes it easier to find the latest data without first grouping to find the latest entry. When export_statistics table grows to a high number of million rows, it saves alot of cpu power for the database server.'}

    dbalias = Column(String(256), primary_key=True, nullable=False, comment='ID of the Database Connection')
    target_database = Column(String(256), nullable=False, comment='Name of the source database')
    target_schema = Column(String(256), primary_key=True, nullable=False, comment='Name of the source schema')
    target_table = Column(String(256), primary_key=True, nullable=False, comment='Name of the source table')
    hive_db = Column(String(256), comment='Hive Database')
    hive_table = Column(String(256), comment='Hive Table')
    export_phase = Column(String(32), comment='Import Phase method')
    incremental = Column(TINYINT(4), comment='0 = Full import, 1 = Incremental import')
    rows = Column(BIGINT(20), comment='How many rows that was imported')
    size = Column(BIGINT(20), comment='The total size in bytes that was imported')
    sessions = Column(TINYINT(4), comment='How many parallell sessions was used against the source (sqoop mappers)')
    duration = Column(INTEGER(11), comment='Tota duration in seconds')
    start = Column(DateTime, comment='Timestamp of start')
    stop = Column(DateTime, comment='Timestamp of stop')
    get_hive_tableschema_duration = Column(INTEGER(11))
    get_hive_tableschema_start = Column(DateTime)
    get_hive_tableschema_stop = Column(DateTime)
    clear_table_rowcount_duration = Column(INTEGER(11))
    clear_table_rowcount_start = Column(DateTime)
    clear_table_rowcount_stop = Column(DateTime)
    create_temp_table_duration = Column(INTEGER(11))
    create_temp_table_start = Column(DateTime)
    create_temp_table_stop = Column(DateTime)
    truncate_temp_table_duration = Column(INTEGER(11))
    truncate_temp_table_start = Column(DateTime)
    truncate_temp_table_stop = Column(DateTime)
    fetch_maxvalue_start = Column(DateTime)
    fetch_maxvalue_stop = Column(DateTime)
    fetch_maxvalue_duration = Column(INTEGER(11))
    insert_into_temp_table_duration = Column(INTEGER(11))
    insert_into_temp_table_start = Column(DateTime)
    insert_into_temp_table_stop = Column(DateTime)
    create_target_table_duration = Column(INTEGER(11))
    create_target_table_start = Column(DateTime)
    create_target_table_stop = Column(DateTime)
    truncate_target_table_duration = Column(INTEGER(11))
    truncate_target_table_start = Column(DateTime)
    truncate_target_table_stop = Column(DateTime)
    sqoop_duration = Column(INTEGER(11))
    sqoop_start = Column(DateTime)
    sqoop_stop = Column(DateTime)
    validate_duration = Column(INTEGER(11))
    validate_start = Column(DateTime)
    validate_stop = Column(DateTime)


class exportTables(Base):
    __tablename__ = 'export_tables'
    __table_args__ = {'comment': 'Main table where all tables that we can export are stored. '}

    dbalias = Column(String(256), primary_key=True, nullable=False, comment='Database connection name that we export to')
    target_schema = Column(String(256), primary_key=True, nullable=False, comment='Schema on the target system')
    target_table = Column(String(256), primary_key=True, nullable=False, comment='Table on the target system')
    table_id = Column(INTEGER(10), nullable=False, unique=True, autoincrement=True, comment='Unique identifier of the table')
    export_type = Column(String(16), nullable=False, comment='What export method to use. Only full and incr is supported.', server_default=text("'full'"))
    hive_db = Column(String(256), nullable=False, comment='Name of Hive Database that we export from')
    hive_table = Column(String(256), nullable=False, comment='Name of Hive Table that we export from')
    last_update_from_hive = Column(DateTime, comment='Timestamp of last schema update from Hive')
    sql_where_addition = Column(String(1024), comment='Will be added AFTER the SQL WHERE. If it\'s an incr export, this will be after the incr limit statements. Example "orderId > 1000"')
    include_in_airflow = Column(TINYINT(4), nullable=False, comment='Will the table be included in Airflow DAG when it matches the DAG selection', server_default=text("'1'"))
    export_history = Column(TINYINT(4), nullable=False, comment='<NOT USED>', server_default=text("'0'"))
    source_is_view = Column(TINYINT(4), nullable=False, comment='<NOT USED>', server_default=text("'0'"))
    source_is_acid = Column(TINYINT(4), nullable=False, comment='<NOT USED>', server_default=text("'0'"))
    validate_export = Column(TINYINT(4), nullable=False, comment="1 = Validate the export once it's done. 0 = Disable validation", server_default=text("'1'"))
    uppercase_columns = Column(TINYINT(4), nullable=False, comment='-1 = auto (Oracle = uppercase, other databases = lowercase)', server_default=text("'-1'"))
    truncate_target = Column(TINYINT(4), nullable=False, comment='1 = Truncate the target table before we export the data. Not used by incremental exports', server_default=text("'1'"))
    mappers = Column(TINYINT(4), nullable=False, comment="-1 = auto, 0 = invalid. Auto updated by 'export_main.sh'", server_default=text("'-1'"))
    hive_rowcount = Column(BIGINT(20), comment='Number of rows in Hive table. Dont change manually')
    target_rowcount = Column(BIGINT(20), comment='Number of rows in Target table. Dont change manually')
    incr_column = Column(String(256), comment='The column in the Hive table that will be used to identify new rows for the incremental export. Must be a timestamp column')
    incr_validation_method = Column(Enum('full', 'incr'), comment='full or incr. Full means that the validation will check to total number of rows up until maxvalue and compare source with target. Incr will only compare the rows between min and max value (the data that sqoop just wrote)', server_default=text("'full'"))
    incr_minvalue = Column(String(25), comment='Used by incremental exports to keep track of progress. Dont change manually')
    incr_maxvalue = Column(String(25), comment='Used by incremental exports to keep track of progress. Dont change manually')
    incr_minvalue_pending = Column(String(25), comment='Used by incremental exports to keep track of progress. Dont change manually')
    incr_maxvalue_pending = Column(String(25), comment='Used by incremental exports to keep track of progress. Dont change manually')
    sqoop_options = Column(String(1024), comment='Sqoop options to use during export.')
    sqoop_last_size = Column(BIGINT(20), comment='Used to track sqoop operation. Dont change manually')
    sqoop_last_rows = Column(BIGINT(20), comment='Used to track sqoop operation. Dont change manually')
    sqoop_last_mappers = Column(TINYINT(4), comment='Used to track sqoop operation. Dont change manually')
    sqoop_last_execution = Column(BIGINT(20), comment='Used to track sqoop operation. Dont change manually')
    create_target_table_sql = Column(Text, comment='SQL statement that was used to create the target table. Dont change manually')
    operator_notes = Column(Text, comment='Free text field to write a note about the export. ')


class importFailureLog(Base):
    __tablename__ = 'import_failure_log'
    __table_args__ = {'comment': 'If there is an error or a warning during import, bu the import still continues, these errors are logged in this table. An example could be that  a column cant be altered, foreign key not created, no new columns can be added and such.'}

    hive_db = Column(String(256), primary_key=True, nullable=False, comment='Hive Database')
    hive_table = Column(String(256), primary_key=True, nullable=False, comment='Hive Table')
    eventtime = Column(DateTime, nullable=False, comment='Time when error/warning occurred', server_default=text("CURRENT_TIMESTAMP"))
    severity = Column(Text, comment='The Severity of the event. ')
    import_type = Column(Text, comment='The import method used')
    error_text = Column(Text, comment='Text describing the failure')



#t_import_foreign_keys_VIEW = Table(
#    'import_foreign_keys_VIEW', metadata,
#    Column('hive_db', String(256)),
#    Column('hive_table', String(256)),
#    Column('fk_index', INTEGER(10)),
#    Column('column_name', String(256)),
#    Column('ref_hive_Db', String(256)),
#    Column('ref_hive_table', String(256)),
#    Column('ref_column_name', String(256))
#)


class importRetriesLog(Base):
    __tablename__ = 'import_retries_log'
    __table_args__ = {'comment': 'Log of all retries that have happened. '}

    hive_db = Column(String(256), primary_key=True, nullable=False, comment='Hive DB')
    hive_table = Column(String(256), primary_key=True, nullable=False, comment='Hive Table')
    retry_time = Column(DateTime, primary_key=True, nullable=False, comment='Time when the retry was started')
    stage = Column(INTEGER(11), nullable=False, comment="The stage of the import that the retry started from. This is an internal stage and has nothing to do with stage1 and stage2 in Airflow DAG's")
    stage_description = Column(Text, nullable=False, comment='Description of the stage')
    import_type = Column(Text, comment='<NOT USED>')
    unrecoverable_error = Column(TINYINT(4), comment='<NOT USED>')
    get_source_rowcount_start = Column(DateTime, comment='<NOT USED>')
    get_source_rowcount_stop = Column(DateTime, comment='<NOT USED>')
    get_source_rowcount_duration = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_start = Column(DateTime, comment='<NOT USED>')
    sqoop_stop = Column(DateTime, comment='<NOT USED>')
    sqoop_duration = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_mappers = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_rows = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_size = Column(BIGINT(20), comment='<NOT USED>')
    source_table_rowcount = Column(BIGINT(20), comment='<NOT USED>')
    target_table_rowcount = Column(BIGINT(20), comment='<NOT USED>')
    incr_minvalue = Column(Text, comment='<NOT USED>')
    incr_maxvalue = Column(Text, comment='<NOT USED>')
    incr_column = Column(Text, comment='<NOT USED>')
    logdir = Column(Text, comment='<NOT USED>')
    timefile = Column(Text, comment='<NOT USED>')


class importStage(Base):
    __tablename__ = 'import_stage'
    __table_args__ = {'comment': 'The import tool keeps track of how far in the import the tool have succeeded. So in case of an error, lets say that Hive is not responding, the next time an import is executed it will skip the first part and continue from where it ended in error on the previous run. If you want to rerun from the begining, the information in this table needs to be cleared. This is done with the "manage --clearImportStage" tool. Keep in mind that clearing the stage of an incremental import might result in the loss of the data.'}

    hive_db = Column(String(256), primary_key=True, nullable=False, comment='Hive Database')
    hive_table = Column(String(256), primary_key=True, nullable=False, comment='Hive Table')
    stage = Column(INTEGER(11), primary_key=True, nullable=False, comment="Current stage of the import. This is an internal stage and has nothing to do with stage1 and stage2 in Airflow DAG's")
    stage_description = Column(Text, nullable=False, comment='Description of the stage')
    stage_time = Column(DateTime, comment='The date and time when the import entered the stage')
    import_type = Column(Text, comment='<NOT USED>')
    unrecoverable_error = Column(TINYINT(4), comment='<NOT USED>')
    get_source_rowcount_start = Column(DateTime, comment='<NOT USED>')
    get_source_rowcount_stop = Column(DateTime, comment='<NOT USED>')
    get_source_rowcount_duration = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_start = Column(DateTime, comment='<NOT USED>')
    sqoop_stop = Column(DateTime, comment='<NOT USED>')
    sqoop_duration = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_mappers = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_rows = Column(BIGINT(20), comment='<NOT USED>')
    sqoop_size = Column(BIGINT(20), comment='<NOT USED>')
    source_table_rowcount = Column(BIGINT(20), comment='<NOT USED>')
    target_table_rowcount = Column(BIGINT(20), comment='<NOT USED>')
    incr_minvalue = Column(Text, comment='<NOT USED>')
    incr_maxvalue = Column(Text, comment='<NOT USED>')
    incr_column = Column(Text, comment='<NOT USED>')
    logdir = Column(Text, comment='<NOT USED>')
    timefile = Column(Text, comment='<NOT USED>')


class importStageStatistic(Base):
    __tablename__ = 'import_stage_statistics'
    __table_args__ = {'comment': 'As DBImport progress through the different stages of the import, it also keeps track of start and stop time for each stage together with the duration. That information is kept in this table'}

    hive_db = Column(String(256), primary_key=True, nullable=False, comment='Hive Database')
    hive_table = Column(String(256), primary_key=True, nullable=False, comment='Hive Table')
    stage = Column(INTEGER(11), primary_key=True, nullable=False, comment="Current stage of the import. This is an internal stage and has nothing to do with stage1 and stage2 in Airflow DAG's")
    start = Column(DateTime, nullable=False, comment='Time when stage started')
    stop = Column(DateTime, nullable=False, comment='Time when stage was completed')
    duration = Column(INTEGER(11), nullable=False, comment='Duration of stage')


class importStatistic(Base):
    __tablename__ = 'import_statistics'
    __table_args__ = (
        Index('hive_db_hive_table', 'hive_db', 'hive_table'),
        {'comment': "At the end of each import, all statistics about how long each part took aswell as general information about Hive datbase and table, number of rows imported, size of the import and much more are logged in this table. This table grows and will never be truncated by DBImport itself. If it becomes to large for you, it's up to each user to delete or truncate this table as you see fit."}
    )

    id = Column(BIGINT(20), primary_key=True, autoincrement=True, comment='Auto incremented PrimaryKey of the table')
    hive_db = Column(String(256), comment='Hive Database')
    hive_table = Column(String(256), comment='Hive Table')
    importtype = Column(String(32), comment='What kind of import type that was used')
    import_phase = Column(String(32), comment='Import Phase method')
    copy_phase = Column(String(32), comment='Copy Phase method')
    etl_phase = Column(String(32), comment='ETL Phase method')
    incremental = Column(TINYINT(4), comment='0 = Full import, 1 = Incremental import')
    dbalias = Column(String(256), comment='ID of the Database Connection')
    source_database = Column(String(256), comment='Name of the source database')
    source_schema = Column(String(256), comment='Name of the source schema')
    source_table = Column(String(256), comment='Name of the source table')
    rows = Column(BIGINT(20), comment='How many rows that was imported')
    size = Column(BIGINT(20), comment='The total size in bytes that was imported')
    sessions = Column(TINYINT(4), comment='How many parallell sessions was used against the source (sqoop mappers)')
    duration = Column(INTEGER(11), comment='Tota duration in seconds')
    start = Column(DateTime, comment='Timestamp of start')
    stop = Column(DateTime, comment='Timestamp of stop')
    sqoop_duration = Column(INTEGER(11))
    sqoop_start = Column(DateTime)
    sqoop_stop = Column(DateTime)
    clear_hive_locks_duration = Column(INTEGER(11))
    clear_hive_locks_start = Column(DateTime)
    clear_hive_locks_stop = Column(DateTime)
    clear_table_rowcount_duration = Column(INTEGER(11))
    clear_table_rowcount_start = Column(DateTime)
    clear_table_rowcount_stop = Column(DateTime)
    connect_to_hive_duration = Column(INTEGER(11))
    connect_to_hive_start = Column(DateTime)
    connect_to_hive_stop = Column(DateTime)
    create_import_table_duration = Column(INTEGER(11))
    create_import_table_start = Column(DateTime)
    create_import_table_stop = Column(DateTime)
    create_target_table_duration = Column(INTEGER(11))
    create_target_table_start = Column(DateTime)
    create_target_table_stop = Column(DateTime)
    get_import_rowcount_duration = Column(INTEGER(11))
    get_import_rowcount_start = Column(DateTime)
    get_import_rowcount_stop = Column(DateTime)
    get_source_rowcount_duration = Column(INTEGER(11))
    get_source_rowcount_start = Column(DateTime)
    get_source_rowcount_stop = Column(DateTime)
    get_source_tableschema_duration = Column(INTEGER(11))
    get_source_tableschema_start = Column(DateTime)
    get_source_tableschema_stop = Column(DateTime)
    get_target_rowcount_duration = Column(INTEGER(11))
    get_target_rowcount_start = Column(DateTime)
    get_target_rowcount_stop = Column(DateTime)
    hive_import_duration = Column(INTEGER(11))
    hive_import_start = Column(DateTime)
    hive_import_stop = Column(DateTime)
    truncate_target_table_duration = Column(INTEGER(11))
    truncate_target_table_start = Column(DateTime)
    truncate_target_table_stop = Column(DateTime)
    merge_table_duration = Column(INTEGER(11))
    merge_table_start = Column(DateTime)
    merge_table_stop = Column(DateTime)
    create_history_table_duration = Column(INTEGER(11))
    create_history_table_start = Column(DateTime)
    create_history_table_stop = Column(DateTime)
    create_delete_table_duration = Column(INTEGER(11))
    create_delete_table_start = Column(DateTime)
    create_delete_table_stop = Column(DateTime)
    update_statistics_duration = Column(INTEGER(11))
    update_statistics_start = Column(DateTime)
    update_statistics_stop = Column(DateTime)
    validate_import_table_duration = Column(INTEGER(11))
    validate_import_table_start = Column(DateTime)
    validate_import_table_stop = Column(DateTime)
    validate_sqoop_import_duration = Column(INTEGER(11))
    validate_sqoop_import_start = Column(DateTime)
    validate_sqoop_import_stop = Column(DateTime)
    validate_target_table_duration = Column(INTEGER(11))
    validate_target_table_start = Column(DateTime)
    validate_target_table_stop = Column(DateTime)


class importStatisticsLast(Base):
    __tablename__ = 'import_statistics_last'
    __table_args__ = (
        Index('hive_db_hive_table', 'hive_db', 'hive_table'),
        {'comment': "The last entry in table import_statistics is also stored in this table. This makes it easier to find the latest data without first grouping to find the latest entry. When import_statistics table grows to a high number of million rows, it saves alot of cpu power for the database server."}
    )
    
    hive_db = Column( String(256), primary_key=True, comment='Hive Database')
    hive_table = Column( String(256), primary_key=True, comment='Hive Table')
    importtype = Column( String(32), comment='What kind of import type that was used')
    import_phase = Column( String(32), comment='Import Phase method')
    copy_phase = Column( String(32), comment='Copy Phase method')
    etl_phase = Column( String(32), comment='ETL Phase method')
    incremental = Column( TINYINT(4), comment='0 = Full import, 1 = Incremental import')
    dbalias = Column( String(256), comment='ID of the Database Connection')
    source_database = Column( String(256), comment='Name of the source database')
    source_schema = Column( String(256), comment='Name of the source schema')
    source_table = Column( String(256), comment='Name of the source table')
    rows = Column( BIGINT(20), comment='How many rows that was imported')
    size = Column( BIGINT(20), comment='The total size in bytes that was imported')
    sessions = Column( TINYINT(4), comment='How many parallell sessions was used against the source (sqoop mappers)')
    duration = Column( INTEGER(11), comment='Tota duration in seconds')
    start = Column( DateTime, comment='Timestamp of start')
    stop = Column( DateTime, comment='Timestamp of stop')
    sqoop_duration = Column( INTEGER(11))
    sqoop_start = Column( DateTime)
    sqoop_stop = Column( DateTime)
    clear_hive_locks_duration = Column( INTEGER(11))
    clear_hive_locks_start = Column( DateTime)
    clear_hive_locks_stop = Column( DateTime)
    clear_table_rowcount_duration = Column( INTEGER(11))
    clear_table_rowcount_start = Column( DateTime)
    clear_table_rowcount_stop = Column( DateTime)
    connect_to_hive_duration = Column( INTEGER(11))
    connect_to_hive_start = Column( DateTime)
    connect_to_hive_stop = Column( DateTime)
    create_import_table_duration = Column( INTEGER(11))
    create_import_table_start = Column( DateTime)
    create_import_table_stop = Column( DateTime)
    create_target_table_duration = Column( INTEGER(11))
    create_target_table_start = Column( DateTime)
    create_target_table_stop = Column( DateTime)
    get_import_rowcount_duration = Column( INTEGER(11))
    get_import_rowcount_start = Column( DateTime)
    get_import_rowcount_stop = Column( DateTime)
    get_source_rowcount_duration = Column( INTEGER(11))
    get_source_rowcount_start = Column( DateTime)
    get_source_rowcount_stop = Column( DateTime)
    get_source_tableschema_duration = Column( INTEGER(11))
    get_source_tableschema_start = Column( DateTime)
    get_source_tableschema_stop = Column( DateTime)
    get_target_rowcount_duration = Column( INTEGER(11))
    get_target_rowcount_start = Column( DateTime)
    get_target_rowcount_stop = Column( DateTime)
    hive_import_duration = Column( INTEGER(11))
    hive_import_start = Column( DateTime)
    hive_import_stop = Column( DateTime)
    truncate_target_table_duration = Column( INTEGER(11))
    truncate_target_table_start = Column( DateTime)
    truncate_target_table_stop = Column( DateTime)
    merge_table_duration = Column( INTEGER(11))
    merge_table_start = Column( DateTime)
    merge_table_stop = Column( DateTime)
    create_history_table_duration = Column( INTEGER(11))
    create_history_table_start = Column( DateTime)
    create_history_table_stop = Column( DateTime)
    create_delete_table_duration = Column( INTEGER(11))
    create_delete_table_start = Column( DateTime)
    create_delete_table_stop = Column( DateTime)
    update_statistics_duration = Column( INTEGER(11))
    update_statistics_start = Column( DateTime)
    update_statistics_stop = Column( DateTime)
    validate_import_table_duration = Column( INTEGER(11))
    validate_import_table_start = Column( DateTime)
    validate_import_table_stop = Column( DateTime)
    validate_sqoop_import_duration = Column( INTEGER(11))
    validate_sqoop_import_start = Column( DateTime)
    validate_sqoop_import_stop = Column( DateTime)
    validate_target_table_duration = Column( INTEGER(11))
    validate_target_table_start = Column( DateTime)
    validate_target_table_stop = Column( DateTime)



class importTables(Base):
    __tablename__ = 'import_tables'
    __table_args__ = (
        Index('hive_db_dbalias_source_schema_source_table', 'hive_db', 'dbalias', 'source_schema', 'source_table'),
        {'comment': 'Main table where all tables that we can import are stored. '}
    )

    hive_db = Column(String(256), primary_key=True, nullable=False, comment='Hive Database to import to')
    hive_table = Column(String(256), primary_key=True, nullable=False, comment='Hive Table to import to')
    table_id = Column(INTEGER(10), nullable=False, unique=True, autoincrement=True, comment='Unique identifier')
    dbalias = Column(String(256), nullable=False, comment='Name of database connection from jdbc_connections table')
    source_schema = Column(String(256), nullable=False, comment='Name of the schema in the remote database')
    source_table = Column(String(256), nullable=False, comment='Name of the table in the remote database')
    import_type = Column(String(32), nullable=False, comment='What import method to use', server_default=text("'full'"))
    last_update_from_source = Column(DateTime, comment='Timestamp of last schema update from source')
    sqoop_sql_where_addition = Column(String(1024), comment='Will be added AFTER the SQL WHERE. If it\'s an incr import, this will be after the incr limit statements. Example "orderId > 1000"')
    nomerge_ingestion_sql_addition = Column(String(2048), comment='This will be added to the data ingestion of None-Merge imports (full, full_direct and incr). Usefull to filter out data from import tables to target tables')
    include_in_airflow = Column(TINYINT(4), nullable=False, comment='Will the table be included in Airflow DAG when it matches the DAG selection', server_default=text("'1'"))
    airflow_priority = Column(TINYINT(4), comment='This will set priority_weight in Airflow')
    validate_import = Column(TINYINT(4), nullable=False, comment='Should the import be validated', server_default=text("'1'"))
    validate_source = Column(Enum('query', 'sqoop'), comment="query = Run a 'select count(*) from ...' to get the number of rows in the source table. sqoop = Use the number of rows imported by sqoop as the number of rows in the source table", server_default=text("'query'"))
    validate_diff_allowed = Column(BIGINT(20), nullable=False, comment='-1 = auto calculated diff allowed. If a positiv number, this is the amount of rows that the diff is allowed to have', server_default=text("'-1'"))
    truncate_hive = Column(TINYINT(4), nullable=False, comment='Truncate Hive table before loading it. ', server_default=text("'1'"))
    mappers = Column(TINYINT(4), nullable=False, comment="-1 = auto or positiv number for a fixed number of mappers. If Auto, then it's calculated based of last sqoop import size", server_default=text("'-1'"))
    soft_delete_during_merge = Column(TINYINT(4), nullable=False, comment='If 1, then the row will be marked as deleted instead of actually being removed from the table. Only used for Merge imports', server_default=text("'0'"))
    source_rowcount = Column(BIGINT(20), comment='Used for validation. Dont change manually')
    source_rowcount_incr = Column(BIGINT(20))
    hive_rowcount = Column(BIGINT(20), comment='Used for validation. Dont change manually')
    incr_mode = Column(String(16), comment='append or lastmodified')
    incr_column = Column(String(256), comment='What column to use to identify new rows')
    incr_validation_method = Column(Enum('full', 'incr'), comment='full or incr. Full means that the validation will check to total number of rows up until maxvalue and compare source with target. Incr will only compare the rows between min and max value (the data that sqoop just wrote)', server_default=text("'full'"))
    incr_minvalue = Column(String(32), comment='Used for incremental imports. Dont change manually')
    incr_maxvalue = Column(String(32), comment='Used for incremental imports. Dont change manually')
    incr_minvalue_pending = Column(String(32), comment='Used for incremental imports. Dont change manually')
    incr_maxvalue_pending = Column(String(32), comment='Used for incremental imports. Dont change manually')
    pk_column_override = Column(String(1024), comment='Force the import and Hive table to define another PrimaryKey constraint. Comma separeted list of columns')
    pk_column_override_mergeonly = Column(String(1024), comment='Force the import to use another PrimaryKey constraint during Merge operations. Comma separeted list of columns')
    hive_merge_heap = Column(INTEGER(11), comment='Should be a multiple of Yarn container size. If NULL then it will use the default specified in Yarn and TEZ')
    concatenate_hive_table = Column(TINYINT(4), nullable=False, comment='<NOT USED>', server_default=text("'-1'"))
    sqoop_query = Column(Text, comment='Use a custom query in sqoop to read data from source table')
    sqoop_options = Column(Text, comment='Options to send to sqoop. Most common used for --split-by option')
    sqoop_last_size = Column(BIGINT(20), comment='Used to track sqoop operation. Dont change manually')
    sqoop_last_rows = Column(BIGINT(20), comment='Used to track sqoop operation. Dont change manually')
    sqoop_last_mappers = Column(TINYINT(4), comment='Used to track sqoop operation. Dont change manually')
    sqoop_last_execution = Column(BIGINT(20), comment='Used to track sqoop operation. Dont change manually')
    sqoop_use_generated_sql = Column(TINYINT(4), nullable=False, comment='1 = Use the generated SQL that is saved in the generated_sqoop_query column', server_default=text("'-1'"))
    sqoop_allow_text_splitter = Column(TINYINT(4), nullable=False, comment='Allow splits on text columns. Use with caution', server_default=text("'0'"))
    force_string = Column(TINYINT(4), nullable=False, comment='If set to 1, all character based fields (char, varchar) will become string in Hive. Overrides the same setting in jdbc_connections table', server_default=text("'-1'"))
    comment = Column(Text, comment='Table comment from source system. Dont change manually')
    generated_hive_column_definition = Column(Text, comment='Generated column definition for Hive create table. Dont change manually')
    generated_sqoop_query = Column(Text, comment='Generated query for sqoop. Dont change manually')
    generated_sqoop_options = Column(Text, comment='Generated options for sqoop. Dont change manually')
    generated_pk_columns = Column(Text, comment='Generated Primary Keys. Dont change manually')
    generated_foreign_keys = Column(Text, comment='<NOT USED>')
    datalake_source = Column(String(256), comment='This value will come in the dbimport_source column if present. Overrides the same setting in jdbc_connections table')
    operator_notes = Column(Text, comment='Free text field to write a note about the import. ')


class jdbcConnection(Base):
    __tablename__ = 'jdbc_connections'
    __table_args__ = {'comment': 'Database connection definitions'}

    dbalias = Column(String(256), primary_key=True, comment='Name of the Database connection')
    private_key_path = Column(String(128), comment='<NOT USED>')
    public_key_path = Column(String(128), comment='<NOT USED>')
    jdbc_url = Column(Text, nullable=False, comment='The JDBC URL String')
    credentials = Column(Text, comment='Encrypted fields for credentials.m Changed by the saveCredentialTool')
    datalake_source = Column(String(256), comment='This value will come in the dbimport_source column if present. Priority is table, connection')
    max_import_sessions = Column(TINYINT(4), comment='You can limit the number of parallel sessions during import with this value. If NULL, then Max will come from configuration file')
    force_string = Column(TINYINT(4), nullable=False, comment='If set to 1, all character based fields (char, varchar) will become string in Hive', server_default=text("'0'"))
    create_datalake_import = Column(TINYINT(4), nullable=False, comment='If set to 1, the datalake_import column will be created on all tables that is using this dbalias', server_default=text("'1'"))
    timewindow_start = Column(Time, comment='Start of the time window when we are allowed to run against this connection.')
    timewindow_stop = Column(Time, comment='End of the time window when we are allowed to run against this connection.')
    operator_notes = Column(Text, comment='Free text field to write a note about the connection')


class jdbcConnectionsDrivers(Base):
    __tablename__ = 'jdbc_connections_drivers'

    database_type = Column(Enum('DB2 AS400', 'DB2 UDB', 'MySQL', 'Oracle', 'PostgreSQL', 'Progress DB', 'SQL Server'), primary_key=True, nullable=False, comment='Name of database type.  Name is hardcoded into Python scripts, so use only defined values')
    version = Column(String(16), primary_key=True, nullable=False, comment='Free-text field with version. Has nothing to do with version of driver itself.')
    driver = Column(String(128), nullable=False, comment='Java class for JDBC driver')
    classpath = Column(String(255), nullable=False, comment='Full path to JDBC driver/jar file. If more than one file is required, separate them with : and no spaces')


class jdbcTableChangeHistory(Base):
    __tablename__ = 'jdbc_table_change_history'
    __table_args__ = (
        Index('dbalias_database_schema_table', 'dbalias', 'db_name', 'schema_name', 'table_name'),
        {'comment': "This table keeps track of all changes that was done to a JDBC table after the initial creation. Example could be that a colum type was changed from char(10) to varchar(10). That kind of information is logged in this table"}
    )

    dbalias = Column( String(256), primary_key=True, nullable=False, comment='Database connection name')
    db_name = Column( String(256), nullable=False, comment='Database name')
    schema_name = Column( String(256), primary_key=True, nullable=False, comment='Schema Name')
    table_name = Column( String(256), primary_key=True, nullable=False, comment='Table Name')
    column_name = Column( String(256), nullable=False, comment='Column Name')
    eventtime = Column( DateTime, nullable=False, comment='Time and date of the event')
    event = Column( String(128), nullable=False, comment='Event name.')
    previous_value = Column( String(256), comment='Value before the change')
    value = Column( String(256), comment='Value after the change')
    description = Column( String(512), nullable=False, comment='Detailed description of the event')



class jsonToRest(Base):
    __tablename__ = 'json_to_rest'
    __table_args__ = {'comment': 'Temporary storage of JSON payloads that will be sent to a REST interface if the tool is configured to do so.'}

    id = Column(BIGINT(20), primary_key=True, autoincrement=True, comment='Unique Identifier')
    type = Column(String(50), nullable=False, comment="The type of JSON data that is saved in the 'jsondata' column")
    create_time = Column(DateTime, nullable=False, comment='Time when the JSON data was created', server_default=text("CURRENT_TIMESTAMP"))
    status = Column(TINYINT(4), nullable=False, comment='Internal status to keep track of what the status of the transmissions is')
    jsondata = Column(Text, nullable=False, comment='The payload to send')


class tableChangeHistory(Base):
    __tablename__ = 'table_change_history'
    __table_args__ = (
        Index('hive_db_hive_table', 'hive_db', 'hive_table'),
        {'comment': "This table keeps track of all changes that was done to an abject after the initial load. Example could be that a colum type was changed from char(10) to varchar(10). That kind of information is logged in this table"}
    )

    hive_db = Column( String(256), primary_key=True, nullable=False, comment='Hive Database')
    hive_table = Column( String(256), primary_key=True, nullable=False, comment='Hive Table')
    column_name = Column( String(256), nullable=False, comment='Column Name')
    eventtime = Column( DateTime, nullable=False, comment='Time and date of the event')
    event = Column( String(128), nullable=False, comment='Event name.')
    previous_value = Column( String(256), comment='Value before the change')
    value = Column( String(256), comment='Value after the change')
    description = Column( String(512), nullable=False, comment='Detailed description of the event')



class airflowImportDagExecution(Base):
    __tablename__ = 'airflow_import_dag_execution'

    dag_name = Column( String(64), primary_key=True, nullable=False)
    executionid = Column( ForeignKey('airflow_execution_type.executionid'), nullable=False, index=True)
    task_config = Column( Text, nullable=False)
    task_name = Column( Text)

    airflow_execution_type = relationship('airflowExecutionType')



class airflowImportTaskExecution(Base):
    __tablename__ = 'airflow_import_task_execution'

    hive_db = Column(String(256), primary_key=True, nullable=False)
    hive_table = Column(String(256), primary_key=True, nullable=False)
    stage = Column(TINYINT(4), primary_key=True, nullable=False)
    executionid = Column(ForeignKey('airflow_execution_type.executionid'), nullable=False, index=True)
    task_config = Column(Text, nullable=False)
    task_name = Column(Text)

    airflow_execution_type = relationship('airflowExecutionType')


class airflowTask(Base):
    __tablename__ = 'airflow_tasks'

    dag_name = Column(String(64), primary_key=True, nullable=False)
    task_name = Column(String(64), primary_key=True, nullable=False)
    task_type = Column(Enum('shell script', 'Hive SQL Script', 'JDBC SQL'), nullable=False, index=True, server_default=text("'Hive SQL Script'"))
    placement = Column(Enum('before main', 'after main', 'in main'), nullable=False, server_default=text("'after main'"))
    jdbc_dbalias = Column(ForeignKey('jdbc_connections.dbalias'), index=True, comment="For  'JDBC SQL' Task Type, this specifies what database the SQL should run against")
    hive_db = Column(String(256))
    airflow_pool = Column(String(64))
    airflow_priority = Column(TINYINT(4))
    include_in_airflow = Column(TINYINT(4), nullable=False, server_default=text("'1'"))
    task_dependency_in_main = Column(String(256))
    task_config = Column(String(256))

    jdbc_connection = relationship('jdbcConnection')


class exportColumns(Base):
    __tablename__ = 'export_columns'
    __table_args__ = {'comment': 'This table contains all columns that exists on all tables that we are exporting. Unlike the export_tables table, this one gets created automatically by the export tool'}

    table_id = Column(ForeignKey('export_tables.table_id', ondelete='CASCADE'), primary_key=True, nullable=False, comment="Foreign Key to export_tables column 'table_id'")
    column_id = Column(INTEGER(10), primary_key=True, nullable=False, unique=True, autoincrement=True, comment='Unique identifier')
    column_name = Column(String(256), primary_key=True, nullable=False, comment='Name of column in target table. Dont change this manually')
    column_type = Column(String(2048), comment='Column type from Hive. Dont change this manually')
    column_order = Column(INTEGER(11), comment='The order of the columns. Dont change this manually')
    hive_db = Column(String(256), comment='Only used to make it easier to read the table. No real usage')
    hive_table = Column(String(256), comment='Only used to make it easier to read the table. No real usage')
    target_column_name = Column(String(256), comment='Override the name of column in the target system')
    target_column_type = Column(String(256), comment='Override the column type in the target system')
    last_update_from_hive = Column(DateTime, nullable=False, comment='Timestamp of last schema update from Hive. Dont change this manually')
    last_export_time = Column(DateTime, comment='Timestamp of last export. Dont change this manually')
    selection = Column(String(256), comment='<NOT USED>')
    include_in_export = Column(TINYINT(4), nullable=False, comment='1 = Include column in export, 0 = Exclude column in export', server_default=text("'1'"))
    comment = Column(Text, comment='The column comment from the source system. Dont change this manually')
    operator_notes = Column(Text, comment='Free text field to write a note about the import. ')

    table = relationship('exportTables')


class importColumns(Base):
    __tablename__ = 'import_columns'
    __table_args__ = (
        Index('table_id_source_column_name', 'table_id', 'source_column_name'),
        {'comment': "This table contains all columns that exists on all tables that we are importing. Unlike the import_tables table, this one gets created automatically by the 'Get Source TableSchema' stage. "}
    )

    table_id = Column(ForeignKey('import_tables.table_id', ondelete='CASCADE'), primary_key=True, nullable=False, comment="Foreign Key to import_tables column 'table_id'")
    column_id = Column(INTEGER(10), primary_key=True, nullable=False, unique=True, autoincrement=True, comment='Unique identifier of the column')
    column_order = Column(INTEGER(10), comment='In what order does the column exist in the source system. ')
    column_name = Column(String(256), primary_key=True, nullable=False, comment='Name of column in Hive. Dont change this manually')
    hive_db = Column(String(256), comment='Hive Database')
    hive_table = Column(String(256), comment='Hive Table')
    source_column_name = Column(String(256), nullable=False, comment='Name of column in source system. Dont change this manually')
    column_type = Column(String(2048), nullable=False, comment='Column type in Hive. Dont change this manually')
    source_column_type = Column(String(2048), nullable=False, comment='Column type in source system. Dont change this manually')
    source_database_type = Column(String(256), comment='That database type was the column imported from')
    column_name_override = Column(String(256), comment='Set a custom name of the column in Hive')
    column_type_override = Column(String(256), comment='Set a custom column type in Hive')
    sqoop_column_type = Column(String(256), comment='Used to create a correct --map-column-java setting for sqoop. ')
    force_string = Column(TINYINT(4), nullable=False, comment='If set to 1, all character based fields (char, varchar) will become string in Hive. Overrides the same setting in import_tables and jdbc_connections table', server_default=text("'-1'"))
    include_in_import = Column(TINYINT(4), nullable=False, comment='1 = Include column in import, 0 = Exclude column in import', server_default=text("'1'"))
    source_primary_key = Column(TINYINT(4), comment='Number starting from 1 listing the order of the column in the PK. Dont change this manually')
    last_update_from_source = Column(DateTime, nullable=False, comment='Timestamp of last schema update from source')
    comment = Column(Text, comment='The column comment from the source system')
    operator_notes = Column(Text, comment='Free text field to write a note about the column')

    table = relationship('importTables')


class importForeignKeys(Base):
    __tablename__ = 'import_foreign_keys'
    __table_args__ = (
        ForeignKeyConstraint(['fk_table_id', 'fk_column_id'], ['import_columns.table_id', 'import_columns.column_id'], ondelete='CASCADE'),
        ForeignKeyConstraint(['table_id', 'column_id'], ['import_columns.table_id', 'import_columns.column_id'], ondelete='CASCADE'),
        Index('FK_import_foreign_keys_import_columns_FK', 'fk_table_id', 'fk_column_id'),
        {'comment': 'All foreign key definitions is saved in this table. The information in this table is recreated all the time, so no manually changes are allowed here. For a better understanding of this table, please use the view called import_foreign_keys_view instead'}
    )

    table_id = Column(INTEGER(10), primary_key=True, nullable=False, comment='Table ID in import_tables that have the FK')
    column_id = Column(INTEGER(10), primary_key=True, nullable=False, comment='Column ID in import_columns that have the FK')
    fk_index = Column(INTEGER(10), primary_key=True, nullable=False, comment='Index of FK')
    fk_table_id = Column(INTEGER(10), nullable=False, comment='Table ID in import_tables that the table is having a reference against')
    fk_column_id = Column(INTEGER(10), nullable=False, comment='Column ID in import_columns that the table is having a reference against')
    key_position = Column(INTEGER(10), nullable=False, comment='Position of the key')

    fk_table = relationship('importColumns', primaryjoin='importForeignKeys.fk_table_id == importColumns.table_id')
    table = relationship('importColumns', primaryjoin='importForeignKeys.table_id == importColumns.table_id')

#airflowDagTriggers_statement = select([
#    airflowImportDagExecution.dag_name,
#    airflowImportDagExecution.task_name.label('trigger_name'),
#    airflowImportDagExecution.task_config.label('dag_to_trigger'),
#]).select_from(airflowImportDagExecution.__table__)
#
#airflowDagTriggers_view = create_view('airflow_dag_triggers', airflowDagTriggers_statement, Base.metadata)
#
#class airflowDagTriggers(Base):
#    __table__ = airflowDagTriggers_view
#
#
#
#colSource = aliased(importColumns)
#colRef = aliased(importColumns)
#
#importForeignKeysView_statement = select([
#    colSource.hive_db,
#    colSource.hive_table,
#    importForeignKeys.fk_index,
#    colSource.column_name,
#    colRef.hive_db.label('ref_hive_Db'),
#    colRef.hive_table.label('ref_hive_table'),
#    colRef.column_name.label('ref_column_name')
#]).select_from(importForeignKeys.__table__
#	.join(colSource, (importForeignKeys.table_id == colSource.table_id) & (importForeignKeys.column_id == colSource.column_id))
#	.join(colRef, (importForeignKeys.fk_table_id == colRef.table_id) & (importForeignKeys.fk_column_id == colRef.column_id))
#	).order_by(importForeignKeys.fk_index, importForeignKeys.key_position)
##	)
#
#importForeignKeysView_view = create_view('import_foreign_keys_VIEW', importForeignKeysView_statement, Base.metadata)
#
#class importForeignKeysView(Base):
#    __table__ = importForeignKeysView_view
"""
select 
	`s`.`hive_db` AS `hive_db`,
	`s`.`hive_table` AS `hive_table`,
	`fk`.`fk_index` AS `fk_index`,
	`s`.`column_name` AS `column_name`,
	`ref`.`hive_db` AS `ref_hive_Db`,
	`ref`.`hive_table` AS `ref_hive_table`,
	`ref`.`column_name` AS `ref_column_name` 
from `import_foreign_keys` `fk` 
join `import_columns` `s` on
	`s`.`table_id` = `fk`.`table_id` and `s`.`column_id` = `fk`.`column_id`
join `import_columns` `ref` on 
	`ref`.`table_id` = `fk`.`fk_table_id` and `ref`.`column_id` = `fk`.`fk_column_id`
order by `fk`.`fk_index`,`fk`.`key_position`
"""
