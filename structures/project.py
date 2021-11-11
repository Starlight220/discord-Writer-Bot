import discord, lib, time
from structures.db import Database

class Project:

    def __init__(self, id):

        self.__db = Database.instance()

        record = self.__db.get('projects', {'id': id})
        if record:
            self._id = record['id']
            self._user = record['user']
            self._name = record['name']
            self._shortname = record['shortname']
            self._words = record['words']
            self._status = record['status']
            self._genre = record['genre']
            self._description = record['description']
            self._link = record['link']
            self._image = record['image']
            self._completed = record['completed']

    def get_id(self):
        return self._id

    def is_complete(self):
        return self._completed > 0

    def get_user(self):
        return self._user

    def get_name(self):
        return self._name

    def get_title(self):
        return self.get_name()

    def get_shortname(self):
        return self._shortname

    def get_words(self):
        return self._words

    def get_status(self):
        return self._status

    def get_genre(self):
        return self._genre

    def get_description(self):
        return self._description

    def get_link(self):
        return self._link if self._link != '' else None

    def get_image(self):
        return self._image if self._image != '' else None

    def get_status_emote(self):
        """
        Given the project's status, get the corresponding emote to display
        @return:
        """

        emotes = [
            {'status': 'planning', 'emote': ':thinking:'},
            {'status': 'progress', 'emote': ':writing_hand:'},
            {'status': 'editing', 'emote': ':pencil:'},
            {'status': 'published', 'emote': ':notebook_with_decorative_cover:'},
            {'status': 'finished', 'emote': ':white_check_mark:'},
            {'status': 'abandoned', 'emote': ':wastebasket:'},
        ]

        for status in emotes:
            if status['status'] == self._status:
                return status['emote']
        return ''

    def get_genre_emote(self):
        """
        Given the project's genre, get the corresponding emote to display
        @return:
        """

        emotes = [
            {'genre': 'fantasy', 'emote': ':man_mage:'},
            {'genre': 'scifi', 'emote': ':ringed_planet:'},
            {'genre': 'romance', 'emote': ':heart:'},
            {'genre': 'horror', 'emote': ':skull:'},
            {'genre': 'fiction', 'emote': ':blue_book:'},
            {'genre': 'nonfiction', 'emote': ':bookmark:'},
            {'genre': 'short', 'emote': ':shorts:'},
            {'genre': 'mystery', 'emote': ':detective:'},
            {'genre': 'thriller', 'emote': ':scream:'},
            {'genre': 'crime', 'emote': ':oncoming_police_car:'},
            {'genre': 'erotic', 'emote': ':hot_pepper:'},
            {'genre': 'comic', 'emote': ':art:'},
            {'genre': 'action', 'emote': ':gun:'},
            {'genre': 'drama', 'emote': ':performing_arts:'},
            {'genre': 'fanfic', 'emote': ':art:'},
            {'genre': 'sfw', 'emote': ':green_circle:'},
            {'genre': 'nsfw', 'emote': ':red_circle:'},
            {'genre': 'seminsfw', 'emote': ':orange_circle:'},
            {'genre': 'literary', 'emote': ':notebook_with_decorative_cover:'},
            {'genre': 'adventure', 'emote': ':mountain_snow:'},
            {'genre': 'suspense', 'emote': ':worried:'},
            {'genre': 'ya', 'emote': ':adult:'},
            {'genre': 'kids', 'emote': ':children_crossing:'},

        ]

        for genre in emotes:
            if genre['genre'] == self._genre:
                return genre['emote']
        return ''

    def delete(self):
        """
        Delete the project
        :return:
        """
        return self.__db.delete('projects', {'id': self._id})

    def add_words(self, amount):
        """
        Add words to the word count
        :param amount:
        :return:
        """
        self._words += int(amount)
        return self.__db.update('projects', {'words': self._words}, {'id': self._id})

    def update(self, amount):
        """
        Update the word count of the project
        :param amount:
        :return:
        """
        self._words = amount
        return self.__db.update('projects', {'words': amount}, {'id': self._id})

    def rename(self, shortname, name):
        """
        Rename a project
        :param shortname:
        :param name:
        :return:
        """
        self._shortname = shortname
        self._name = name
        return self.__db.update('projects', {'shortname': shortname, 'name': name}, {'id': self._id})

    def set_image(self, img):
        """
        Set the project's image.
        @param img:
        @return:
        """
        return self.__db.update('projects', {'image': img}, {'id': self._id})


    def set_status(self, status):
        """
        Set the project's status.
        @param status:
        @return:
        """
        params = {'status': status}

        # If we are marking it as finished or published and it's not been marked as completed before, add xp.
        if (status == 'finished' or status == 'published') and not self.is_complete():

            # Mark the project as completed.
            params['completed'] = int(time.time())

        return self.__db.update('projects', params, {'id': self._id})

    def set_link(self, link):
        """
        Set the project's link.
        @param link:
        @return:
        """
        return self.__db.update('projects', {'link': link}, {'id': self._id})

    def set_genre(self, genre):
        """
        Set the project's genre.
        @param genre:
        @return:
        """
        return self.__db.update('projects', {'genre': genre}, {'id': self._id})

    def set_description(self, description):
        """
        Set the project's description.
        @param description:
        @return:
        """
        return self.__db.update('projects', {'description': description}, {'id': self._id})

    def get(user, shortname):
        """
        Try to get a project with a given shortname, for a given user
        :param user:
        :param shortname:
        :return:
        """
        db = Database.instance()
        record = db.get('projects', {'user': user, 'shortname': shortname})
        return Project(record['id']) if record else None

    def all(user, filter_by = None, filter = None):
        """
        Get an array of Projects for a given user, matching any optional filter passed through
        @param filter_by:
        @param filter:
        @return:
        """
        db = Database.instance()

        params = {'user': user}
        if filter_by is not None and filter is not None:
            params[filter_by] = filter

        records = db.get_all('projects', params, ['id'], ['name', 'shortname', 'words'])
        projects = []

        for record in records:
            projects.append(Project(record['id']))

        return projects

    def create(user, shortname, name):
        """
        Create a new project
        :param name:
        :return:
        """
        db = Database.instance()
        return db.insert('projects', {'user': user, 'shortname': shortname, 'name': name})

    async def display(self, context):

        title = self.get_title()
        description = self.get_description()
        link = self.get_link()
        words = str("{:,}".format(self.get_words()))

        if link is not None:
            embed = discord.Embed(title=title, color=discord.Color.green(), description=description, url=link)
        else:
            embed = discord.Embed(title=title, color=discord.Color.green(), description=description)

        if self.get_image() is not None:
            embed.set_thumbnail(url=self.get_image())

        embed.add_field(name=lib.get_string('status', context.guild.id), value=self.get_status_emote() + ' ' + lib.get_string('project:status:'+self.get_status(), context.guild.id), inline=True)

        if self.get_genre() is not None:
            embed.add_field(name=lib.get_string('genre', context.guild.id), value=self.get_genre_emote() + ' ' + lib.get_string('project:genre:'+self.get_genre(), context.guild.id), inline=True)

        embed.add_field(name=lib.get_string('wordcount', context.guild.id), value=words, inline=True)

        return await context.send(embed=embed)
