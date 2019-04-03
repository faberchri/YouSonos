import React from "react";
import {currentTrack, NULL_TRACK, playlistChanged, PlaylistItem, SearchResultTrack, Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import List from '@material-ui/core/List';
import SearchResultEntry from "./SearchResultEntry";


interface State {

    playlistTrackUrls: ReadonlySet<string>;
    currentTrack: Track;
}

const styles = (theme: Theme) => createStyles({
    list: {
        overflowY: 'auto'
    },
});

interface Props extends WithStyles<typeof styles> {
    sortedSearchResultTracks: ReadonlyArray<SearchResultTrack>;
}

class SearchResultList extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.state = {
            currentTrack: NULL_TRACK,
            playlistTrackUrls: new Set()
        };
        this.setPlaylistTrackUrls = this.setPlaylistTrackUrls.bind(this);
        this.setCurrentTrack = this.setCurrentTrack.bind(this);
    }

    componentDidMount() {
        playlistChanged(this.setPlaylistTrackUrls);
        currentTrack(this.setCurrentTrack)
    }

    setPlaylistTrackUrls(items: PlaylistItem[]) {
        const playlistTrackUrls = new Set(items.map(item => item.track.url));
        this.setState({
            playlistTrackUrls: playlistTrackUrls,
            currentTrack: this.state.currentTrack,
        });
    }

    setCurrentTrack(currentTrack: Track) {
        this.setState({
            playlistTrackUrls: this.state.playlistTrackUrls,
            currentTrack: currentTrack,
        });
    }

    render() {
        const {classes} = this.props;
        return (
            <List dense className={classes.list}>
                {this.props.sortedSearchResultTracks.map(searchResultTrack => <SearchResultEntry
                    key={searchResultTrack.index}
                    searchResultTrack={searchResultTrack.track}
                    currentTrack={this.state.currentTrack}
                    playlistTrackUrls={this.state.playlistTrackUrls}/>)}
            </List>
        );
    }
}

export default withStyles(styles)(SearchResultList);
