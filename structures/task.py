import lib, time
from structures.db import Database

class Task:

    def __init__(self, id):
        """
        Load a Task object by its ID
        :param id:
        """
        self.__db = Database.instance()
        self.id = None

        record = self.__db.get('tasks', {'id': id})
        if record:
            self.id = record['id']
            self.type = record['type']
            self.time = record['time']
            self.object = record['object']
            self.object_id = record['objectid']
            self.processing = record['processing']
            self.recurring = record['recurring']
            self.run_every_seconds = record['runeveryseconds']

    def is_valid(self):
        """
        Check if the Task object is valid
        :return:
        """
        return self.id is not None

    def is_recurring(self):
        """
        Check if the task is a recurring one or not
        :return:
        """
        return int(self.recurring) == 1

    def is_processing(self):
        """
        Check if this task is already running
        :return:
        """
        return self.processing == 1

    def start_processing(self, value):
        """
        Mark the task as processing or not
        :param value: 0 or 1
        :return:
        """
        return self.__db.update('tasks', {'processing': value}, {'id': self.id})

    async def run(self, bot):
        """
        Run this task
        TODO: In the future, make this better. For now it will do.
        :return: bool
        """

        # If the task is already processing, don't go any further.
        if self.is_processing():
            return True

        # Mark the task as processing so other shards don't pick it up.
        self.start_processing(1)

        # Build a variable to store the method name to run
        method = 'task_' + str(self.type)

        # Start off with a False and see if we can successfully run and turn that to True
        result = False

        # Sprint tasks.
        if self.object == 'sprint':

            from structures.sprint import Sprint

            sprint = Sprint.get(self.object_id)
            if sprint.exists():
                result = await getattr(sprint, method)(bot)
            else:
                # If the sprint doesn't exist, then we can just delete this task.
                result = True

        elif self.object == 'goal':

            from structures.goal import Goal

            goal = Goal()
            result = await getattr(goal, method)(bot)

        elif self.object == 'event':

            from structures.event import Event

            event = Event(self.object_id)
            if event.is_valid():
                result = await getattr(event, method)(bot)
            else:
                # If the event doesn't exist, then we can just delete this task.
                return True

        elif self.object == 'reminder':

            from structures.reminder import Reminder

            reminder = Reminder()
            result = await getattr(reminder, method)(bot)

        else:
            # Invalid task object. May as well just delete this task.
            lib.out('Invalid task object: ' + self.object)
            result = True

        # If we finished the task, and it's not a recurring one, delete it.
        if result is True and not self.is_recurring():
            self.delete()
        else:
            self.start_processing(0)

        # If it's a recurring task, set its next run time.
        if self.is_recurring():
            self.set_recur()

        return result

    def set_recur(self):
        """
        Set the next time this recurring task should be run
        :return:
        """
        now = int(time.time())
        next = now + int(self.run_every_seconds)
        lib.debug('setting next run time for ' + str(self.id) + ' to: ' + str(next))
        return self.__db.update('tasks', {'time': next}, {'id': self.id})

    def delete(self):
        """
        Delete the task
        :return:
        """
        return self.__db.delete('tasks', {'id': self.id})

    async def execute_all(bot):
        """
        Execute a pass of the scheduled tasks that are currently pending
        :return:
        """
        now = int(time.time())
        db = Database.instance()

        pending = db.get_all_sql('SELECT id FROM tasks WHERE time <= %s ORDER BY id ASC', [now])
        for row in pending:
            task = Task(row['id'])
            if task.is_valid():
                result = await task.run(bot)

    def cancel(object, object_id, type=None):
        """
        Cancel all tasks related to a specific object
        :param object:
        :param object_id:
        :param type:
        :return:
        """
        db = Database.instance()

        params = {'object': object, 'objectid': object_id}
        if type is not None:
            params['type'] = type

        return db.delete('tasks', params)

    def get(type, object, object_id):
        """
        Check to see if a task of this type and object_id already exists
        :return:
        """
        db = Database.instance()
        return db.get('tasks', {'type' : type, 'object': object, 'objectid': object_id})

    def schedule(type, time, object, object_id):
        """
        Schedule the task in the database
        :return:
        """
        db = Database.instance()

        # If this task already exists, just update its time.
        record = Task.get(type, object, object_id)
        if record:
            return db.update('tasks', {'time': time}, {'id': record['id']})
        else:
            # Otherwise, create one.
            return db.insert('tasks', {'type': type, 'time': time, 'object': object, 'objectid': object_id})
