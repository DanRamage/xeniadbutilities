import logging.config
from multiprocessing import Process, Queue, current_process, Event
import time
from sqlalchemy import exc

from .database_settings import DatabaseConfiguration
from .xeniaSQLiteAlchemy import xeniaAlchemy as sl_xeniaAlchemy
from .xeniaSQLAlchemy import xeniaAlchemy


logger = logging.getLogger(__name__)


class MultiProcessDataSaver(Process):
    def __init__(self, database_configuration: DatabaseConfiguration):
        Process.__init__(self)
        self.logger = logger
        self.data_queue = Queue()
        self._stop_event = Event()
        self.database_configuration = database_configuration
        self._database_connection = None

    def run(self):
        logger = None
        try:
            logger = logging.getLogger(__name__)

            process_data = True
            db = None
            if self.database_configuration.db_type == "postgres":
                db = xeniaAlchemy()
                if (db.connectDB(self.database_configuration.connectionstringo,
                                 self.database_configuration.username,
                                 self.database_configuration.password,
                                 self.database_configuration.host,
                                 self.database_configuration.database_name,
                                 False)):
                    logger.info(f"Successfully connect to DB: {self._db_name} at {self._db_host}")
                else:
                    logger.error(f"Unable to connect to DB: {self._db_name} at {self._db_host}. Terminating process.")
                    process_data = False

            elif self.database_configuration.db_type == "sqlite":
                db = sl_xeniaAlchemy()
                if (db.connectDB('sqlite',
                                 None,
                                 None,
                                 self.database_configuration.db_type,
                                 None,
                                 False) == True):
                    logger.info(f"Succesfully connect to DB: {self.file_path}")
                else:
                    logger.error(f"Unable to connect to DB: {self.file_path}. Terminating script.")
                    process_data = False

            if db is not None:
                start_time = time.time()
                rec_count = 0
                while process_data:
                    data_rec = self._data_queue.get()
                    if data_rec is not None:
                        try:
                            db.session.add(data_rec)
                            if (rec_count % self._records_before_commit) == 0:
                                db.session.commit()

                            val = ""
                            if data_rec.m_value is not None:
                                val = "%f" % (data_rec.m_value)
                            logger.debug(
                                f"Adding record Sensor: {data_rec.sensor_id} Datetime: {data_rec.m_date} Value: {val}")

                            if ((rec_count % 10) == 0):
                                try:
                                    logger.debug(f"Approximate record count in DB queue: {self._data_queue.qsize()}")
                                # We get this exception under OSX.
                                except NotImplementedError:
                                    pass

                                rec_count += 1
                        # Trying to add record that already exists.
                        except exc.IntegrityError as e:
                            logger.error(f"Duplicate sensor id: {data_rec.sensor_id} Datetime: {data_rec.m_date}")
                            db.session.rollback()
                        except Exception as e:
                            db.session.rollback()
                            logger.exception(e)

                    else:
                        process_data = False
                        db.session.commit()

                    db.disconnect()
                logger.debug(f"{current_process().name} completed in {time.time() - start_time} seconds.")

        except Exception as e:
            logger.exception(e)