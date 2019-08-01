import React from "react";
import {currentTrack, NULL_TRACK, SearchResultTrack, Track} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import List from '@material-ui/core/List';
import SearchResultEntry from "./SearchResultEntry";

// Types from 'npm i @types/react-infinite-scroller' are not compatible
var InfiniteScroll = require('react-infinite-scroller');


interface State {

    currentTrack: Track;
}

const styles = (theme: Theme) => createStyles({
    list: {
        overflowY: 'auto'
    },
});

interface Props extends WithStyles<typeof styles> {
    sortedSearchResultTracks: ReadonlyArray<SearchResultTrack>,
    loadMore: () => void,
    hasMore: boolean,
}

class SearchResultList extends React.Component<Props, State> {

    constructor(props: Props) {
        super(props);
        this.state = {
            currentTrack: NULL_TRACK,
        };
        this.setCurrentTrack = this.setCurrentTrack.bind(this);
    }

    componentDidMount() {
        currentTrack(this.setCurrentTrack)
    }

    setCurrentTrack(currentTrack: Track) {
        this.setState({
            currentTrack: currentTrack,
        });
    }

    render() {
        const {classes} = this.props;
        return (
            <List dense className={classes.list} >
                <InfiniteScroll
                    loadMore={this.props.loadMore}
                    hasMore={this.props.hasMore}
                    useWindow={false}
                    initialLoad={true}>
                    {this.props.sortedSearchResultTracks.map(searchResultTrack =>
                        <SearchResultEntry
                            key={searchResultTrack.index}
                            searchResultTrack={searchResultTrack.track}
                            currentTrack={this.state.currentTrack}/>)
                    }
                </InfiniteScroll>
            </List>
        );
    }
}

export default withStyles(styles)(SearchResultList);
