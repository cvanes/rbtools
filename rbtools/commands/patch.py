from rbtools.api.errors import APIError
from rbtools.commands import Command, CommandError, Option
from rbtools.utils.filesystem import make_tempfile


class Patch(Command):
    """Applies a specific patch from a RB server.

    The patch file indicated by the request id is downloaded from the
    server and then applied locally."""
    name = "patch"
    author = "The Review Board Project"
    args = "<request-id>"
    option_list = [
        Option("--diff-revision",
               dest="diff_revision",
               default=None,
               help="revision id of diff to be used as patch"),
        Option("--px",
               dest="px",
               default=None,
               help="numerical pX argument for patch"),
        Option("--server",
               dest="server",
               metavar="SERVER",
               config_key="REVIEWBOARD_URL",
               default=None,
               help="specify a different Review Board server to use"),
        Option("--username",
               dest="username",
               metavar="USERNAME",
               config_key="USERNAME",
               default=None,
               help="user name to be supplied to the Review Board server"),
        Option("--password",
               dest="password",
               metavar="PASSWORD",
               config_key="PASSWORD",
               default=None,
               help="password to be supplied to the Review Board server"),
    ]

    def get_patch(self, request_id, api_root, diff_revision=None):
        """Return the diff as a string, the used diff revision and its basedir.

        If a diff revision is not specified, then this will look at the most
        recent diff.
        """
        try:
            diffs = api_root.get_diffs(review_request_id=request_id)
        except APIError, e:
            raise CommandError("Error getting diffs: %s" % e)

        # Use the latest diff if a diff revision was not given.
        # Since diff revisions start a 1, increment by one, and
        # never skip a number, the latest diff revisions number
        # should be equal to the number of diffs.
        if diff_revision is None:
            diff_revision = diffs.total_results

        try:
            diff = diffs.get_item(diff_revision)
            diff_body = diff.get_patch().data
            base_dir = diff.basedir
        except APIError:
            raise CommandError('The specified diff revision does not exist.')

        return diff_body, diff_revision, base_dir

    def apply_patch(self, tool, request_id, diff_revision, diff_file_path,
                    base_dir):
        """Apply patch patch_file and display results to user."""
        print ("Patch is being applied from request %s with diff revision "
               " %s." % (request_id, diff_revision))
        tool.apply_patch(diff_file_path, self.repository_info.base_path,
                              base_dir, self.options.px)

    def main(self, request_id):
        """Run the command."""
        repository_info, tool = self.initialize_scm_tool()
        server_url = self.get_server_url(self.repository_info, self.tool)
        api_client, api_root = self.get_api(server_url)

        # Get the patch, the used patch ID and base dir for the diff
        diff_body, diff_revision, base_dir = self.get_patch(
            request_id,
            self.options.diff_revision)

        tmp_patch_file = make_tempfile(diff_body)

        self.apply_patch(tool, request_id, diff_revision, tmp_patch_file,
                         base_dir)
